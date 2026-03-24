param(
    [string]$BaseUrl = "https://muhammadhassan.tech",
    [string]$ShopDomain = "pmcvp2-tv.myshopify.com",
    [string]$ForeignShopDomain = "other-store.myshopify.com",
    [string]$ReindexAdminToken = "",
    [int]$PerfCount = 10
)

$ErrorActionPreference = "Stop"

$passed = 0
$failed = 0

function Write-TestResult {
    param(
        [string]$Name,
        [bool]$Success,
        [string]$Details = ""
    )

    if ($Success) {
        $script:passed++
        Write-Host "[PASS] $Name" -ForegroundColor Green
    }
    else {
        $script:failed++
        Write-Host "[FAIL] $Name $Details" -ForegroundColor Red
    }
}

function Try-ParseJson {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $null
    }

    try {
        return ($Text | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

function Invoke-Api {
    param(
        [ValidateSet("GET", "POST", "DELETE", "PUT", "PATCH")]
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [string]$RawBody = $null,
        [hashtable]$Headers = @{}
    )

    $uri = "$BaseUrl$Path"

    try {
        $params = @{
            Uri     = $uri
            Method  = $Method
            Headers = $Headers
            UseBasicParsing = $true
        }

        if ($null -ne $Body) {
            $params["ContentType"] = "application/json"
            $params["Body"] = ($Body | ConvertTo-Json -Depth 30)
        }
        elseif ($null -ne $RawBody) {
            $params["ContentType"] = "application/json"
            $params["Body"] = $RawBody
        }

        $response = Invoke-WebRequest @params
        $responseHeaders = @{}
        foreach ($k in $response.Headers.Keys) {
            $responseHeaders[$k] = $response.Headers[$k]
        }

        return [pscustomobject]@{
            Ok      = $true
            Status  = [int]$response.StatusCode
            Data    = (Try-ParseJson -Text $response.Content)
            Raw     = $response.Content
            Headers = $response.Headers
        }
    }
    catch {
        $status = -1
        $raw = $null
        $data = $null
        $responseHeaders = @{}

        if ($_.Exception.Response) {
            try {
                $status = [int]$_.Exception.Response.StatusCode.value__
            }
            catch {
                $status = -1
            }

            try {
                foreach ($k in $_.Exception.Response.Headers.Keys) {
                    $responseHeaders[$k] = $_.Exception.Response.Headers[$k]
                }
            }
            catch {
            }

            try {
                $stream = $_.Exception.Response.GetResponseStream()
                if ($stream) {
                    $reader = New-Object System.IO.StreamReader($stream)
                    $raw = $reader.ReadToEnd()
                    $reader.Close()
                    $data = Try-ParseJson -Text $raw
                }
            }
            catch {
            }
        }

        return [pscustomobject]@{
            Ok      = $false
            Status  = $status
            Data    = $data
            Raw     = $raw
            Headers = $_.Exception.Response.Headers
        }
    }
}

function Get-Header {
    param(
        [hashtable]$Headers,
        [string]$Name
    )

    if ($null -eq $Headers) {
        return $null
    }

    if ($Headers -is [System.Collections.IDictionary]) {
        foreach ($k in $Headers.Keys) {
            if ($k -ieq $Name) {
                return $Headers[$k]
            }
        }
    }
    elseif ($Headers.PSObject.Properties.Name -contains "AllKeys") {
        foreach ($k in $Headers.AllKeys) {
            if ($k -ieq $Name) {
                return $Headers[$k]
            }
        }
    }

    return $null
}

Write-Host "Running FULL Part 3 API tests against $BaseUrl" -ForegroundColor Cyan

# 1) Health
$healthPass = $false
try {
    $healthDirect = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET
    $healthPass = ($null -ne $healthDirect) -and ($healthDirect.status -eq "ok")
}
catch {
    $healthPass = $false
}
Write-TestResult -Name "GET /health" -Success $healthPass

# 2) Header behavior - trace echo + response time header
$customTrace = "tr_manual_$(Get-Random -Minimum 1000 -Maximum 9999)"
$headerTracePass = $false
$headerRespMsPass = $false
try {
    $healthWithHeader = Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET -Headers @{ "X-Trace-Id" = $customTrace } -UseBasicParsing
    $traceHeader = $healthWithHeader.Headers["x-trace-id"]
    $respMsHeader = $healthWithHeader.Headers["x-response-time-ms"]
    $respMsParsed = 0
    $respMsIsInt = [int]::TryParse([string]$respMsHeader, [ref]$respMsParsed)
    $headerTracePass = ($traceHeader -eq $customTrace)
    $headerRespMsPass = ($respMsIsInt -and $respMsParsed -ge 0)
}
catch {
    $headerTracePass = $false
    $headerRespMsPass = $false
}
Write-TestResult -Name "Header: X-Trace-Id echo" -Success $headerTracePass
Write-TestResult -Name "Header: X-Response-Time-Ms present" -Success $headerRespMsPass

# 3) Filter products
$filterBody = @{
    filters = @{ in_stock_only = $true }
    sort = @{ field = "updated_at"; order = "desc" }
    pagination = @{ limit = 5; offset = 0 }
}
$filter = Invoke-Api -Method POST -Path "/filter-products" -Body $filterBody
Write-TestResult -Name "POST /filter-products" -Success ($filter.Ok -and $null -ne $filter.Data.items -and $filter.Data.page.limit -eq 5)

# 4) Search products
$searchBody = @{
    query = "football"
    filters = @{ in_stock_only = $true }
    pagination = @{ limit = 5; offset = 0 }
}
$search = Invoke-Api -Method POST -Path "/search-products" -Body $searchBody
Write-TestResult -Name "POST /search-products" -Success ($search.Ok -and $null -ne $search.Data.items -and $search.Data.page.limit -eq 5)

# 5) Sync lifecycle + idempotency
$productId = Get-Random -Minimum 10000000 -Maximum 99999999
$variantId = $productId + 1
$occurredAt = (Get-Date).ToUniversalTime().ToString("o")

$createdPayload = @{
    shop_domain = $ShopDomain
    event_id = "evt-created-$productId"
    occurred_at = $occurredAt
    payload = @{
        id = $productId
        handle = "test-ball-$productId"
        title = "Test Ball $productId"
        body_html = "<p>Match ball for testing</p>"
        tags = "football,match"
        status = "active"
        vendor = "PitchPro"
        product_type = "Ball"
        variants = @(
            @{ id = $variantId; title = "Default"; price = "29.99"; inventory_quantity = 12 }
        )
        images = @(
            @{ src = "https://example.com/ball.jpg" }
        )
    }
}

$created = Invoke-Api -Method POST -Path "/sync/shopify/product-created" -Body $createdPayload
Write-TestResult -Name "POST /sync/shopify/product-created" -Success ($created.Ok -and $created.Data.status -eq "processed" -and $created.Data.embedding_action -eq "created")

$createdDup = Invoke-Api -Method POST -Path "/sync/shopify/product-created" -Body $createdPayload
Write-TestResult -Name "Idempotency: exact duplicate create skipped" -Success ($createdDup.Ok -and $createdDup.Data.status -eq "skipped" -and $createdDup.Data.embedding_action -eq "skipped")

# idempotency edge: same event_id, different occurred_at => should be processed by current key strategy
$createdEdge = $createdPayload.PSObject.Copy()
$createdEdge.occurred_at = (Get-Date).ToUniversalTime().AddSeconds(1).ToString("o")
$createdEdge.payload = $createdPayload.payload.PSObject.Copy()
$createdEdge.payload.id = $productId + 1000
$createdEdge.payload.handle = "test-ball-edge-$productId"
$createdEdge.payload.title = "Test Ball Edge $productId"

$createdEdgeResult = Invoke-Api -Method POST -Path "/sync/shopify/product-created" -Body $createdEdge
Write-TestResult -Name "Idempotency edge: same event_id + new occurred_at processed" -Success ($createdEdgeResult.Ok -and $createdEdgeResult.Data.status -eq "processed")

$updatedPriceOnly = $createdPayload.PSObject.Copy()
$updatedPriceOnly.event_id = "evt-update-price-$productId"
$updatedPriceOnly.occurred_at = (Get-Date).ToUniversalTime().AddSeconds(2).ToString("o")
$updatedPriceOnly.payload = $createdPayload.payload.PSObject.Copy()
$updatedPriceOnly.payload.variants = @(
    @{ id = $variantId; title = "Default"; price = "31.99"; inventory_quantity = 9 }
)

$updatePrice = Invoke-Api -Method POST -Path "/sync/shopify/product-updated" -Body $updatedPriceOnly
Write-TestResult -Name "POST /sync/shopify/product-updated (price only)" -Success ($updatePrice.Ok -and $updatePrice.Data.status -eq "processed" -and $updatePrice.Data.embedding_action -eq "skipped")

$updatedText = $createdPayload.PSObject.Copy()
$updatedText.event_id = "evt-update-text-$productId"
$updatedText.occurred_at = (Get-Date).ToUniversalTime().AddSeconds(3).ToString("o")
$updatedText.payload = $createdPayload.payload.PSObject.Copy()
$updatedText.payload.title = "Test Ball Updated $productId"
$updatedText.payload.tags = "football,match,premium"
$updatedText.payload.body_html = "<p>Updated match ball description</p>"

$updateText = Invoke-Api -Method POST -Path "/sync/shopify/product-updated" -Body $updatedText
Write-TestResult -Name "POST /sync/shopify/product-updated (text changed)" -Success ($updateText.Ok -and $updateText.Data.status -eq "processed" -and $updateText.Data.embedding_action -eq "updated")

$deleteBody = @{
    shop_domain = $ShopDomain
    event_id = "evt-delete-$productId"
    occurred_at = (Get-Date).ToUniversalTime().AddSeconds(4).ToString("o")
    payload = @{ id = $productId }
}
$deleted = Invoke-Api -Method POST -Path "/sync/shopify/product-deleted" -Body $deleteBody
Write-TestResult -Name "POST /sync/shopify/product-deleted" -Success ($deleted.Ok -and $deleted.Data.status -eq "processed" -and $deleted.Data.embedding_action -eq "deleted")

$gid = "gid://shopify/Product/$productId"
$encodedGid = [System.Uri]::EscapeDataString($gid)
$deleted404Pass = $false
try {
    Invoke-WebRequest -Uri "$BaseUrl/product/$encodedGid" -Method GET -UseBasicParsing | Out-Null
    $deleted404Pass = $false
}
catch {
    try {
        $deleted404Pass = ([int]$_.Exception.Response.StatusCode.value__ -eq 404)
    }
    catch {
        $deleted404Pass = $false
    }
}
Write-TestResult -Name "GET /product/{id} after delete returns 404" -Success $deleted404Pass

# cleanup edge-created product
$edgeDelete = @{
    shop_domain = $ShopDomain
    event_id = "evt-delete-edge-$productId"
    occurred_at = (Get-Date).ToUniversalTime().AddSeconds(5).ToString("o")
    payload = @{ id = ($productId + 1000) }
}
$null = Invoke-Api -Method POST -Path "/sync/shopify/product-deleted" -Body $edgeDelete

# 6) Invalid payload matrix
$badSearch = Invoke-Api -Method POST -Path "/search-products" -Body @{ query = "" }
Write-TestResult -Name "Validation: empty query returns 400" -Success ((-not $badSearch.Ok) -and $badSearch.Status -eq 400)

$badFilterType = Invoke-Api -Method POST -Path "/filter-products" -Body @{ filters = @{ in_stock_only = $true }; sort = @{ field = "updated_at"; order = "desc" }; pagination = @{ limit = "five"; offset = 0 } }
Write-TestResult -Name "Validation: wrong pagination type returns 400" -Success ((-not $badFilterType.Ok) -and $badFilterType.Status -eq 400)

$badDelete = Invoke-Api -Method POST -Path "/sync/shopify/product-deleted" -Body @{ shop_domain = $ShopDomain; event_id = "evt-bad-delete"; payload = @{ } }
Write-TestResult -Name "Validation: delete without payload.id returns 400" -Success ((-not $badDelete.Ok) -and $badDelete.Status -eq 400)

$badJson = Invoke-Api -Method POST -Path "/search-products" -RawBody "{bad-json"
Write-TestResult -Name "Validation: malformed JSON returns 400" -Success ((-not $badJson.Ok) -and $badJson.Status -eq 400)

# 7) Store/domain isolation for search
$foreignProductId = Get-Random -Minimum 11000000 -Maximum 99999999
$foreignVariantId = $foreignProductId + 1
$foreignToken = "foreign-only-$foreignProductId"
$foreignCreate = @{
    shop_domain = $ForeignShopDomain
    event_id = "evt-created-foreign-$foreignProductId"
    occurred_at = (Get-Date).ToUniversalTime().AddSeconds(6).ToString("o")
    payload = @{
        id = $foreignProductId
        handle = "foreign-test-$foreignProductId"
        title = "Foreign Product $foreignToken"
        body_html = "<p>$foreignToken</p>"
        tags = "foreign,test"
        status = "active"
        vendor = "Foreign"
        product_type = "Ball"
        variants = @(
            @{ id = $foreignVariantId; title = "Default"; price = "19.99"; inventory_quantity = 4 }
        )
        images = @(@{ src = "https://example.com/foreign.jpg" })
    }
}
$foreignCreated = Invoke-Api -Method POST -Path "/sync/shopify/product-created" -Body $foreignCreate
$foreignCreatePass = $foreignCreated.Ok -and $foreignCreated.Data.status -eq "processed"
Write-TestResult -Name "Cross-store setup: foreign product created" -Success $foreignCreatePass

$foreignSearch = Invoke-Api -Method POST -Path "/search-products" -Body @{ query = $foreignToken; filters = @{ in_stock_only = $true }; pagination = @{ limit = 10; offset = 0 } }
$foreignLeak = $false
if ($foreignSearch.Ok -and $foreignSearch.Data.items) {
    foreach ($item in $foreignSearch.Data.items) {
        if ($item.id -eq "gid://shopify/Product/$foreignProductId") {
            $foreignLeak = $true
            break
        }
    }
}
Write-TestResult -Name "Cross-store isolation: foreign product not returned in search" -Success (-not $foreignLeak)

# cleanup foreign product
$foreignDelete = @{
    shop_domain = $ForeignShopDomain
    event_id = "evt-delete-foreign-$foreignProductId"
    occurred_at = (Get-Date).ToUniversalTime().AddSeconds(7).ToString("o")
    payload = @{ id = $foreignProductId }
}
$null = Invoke-Api -Method POST -Path "/sync/shopify/product-deleted" -Body $foreignDelete

# 8) Reindex guard and optional auth path
$reindexNoHeader = Invoke-Api -Method POST -Path "/sync/reindex" -Body @{ scope = "all" }
Write-TestResult -Name "POST /sync/reindex guard without token (403 or 500)" -Success ((-not $reindexNoHeader.Ok) -and ($reindexNoHeader.Status -eq 403 -or $reindexNoHeader.Status -eq 500))

if (-not [string]::IsNullOrWhiteSpace($ReindexAdminToken)) {
    $reindexWrong = Invoke-Api -Method POST -Path "/sync/reindex" -Body @{ scope = "all" } -Headers @{ "X-Admin-Token" = "wrong-token" }
    Write-TestResult -Name "POST /sync/reindex wrong token -> 403" -Success ((-not $reindexWrong.Ok) -and $reindexWrong.Status -eq 403)

    $reindexGood = Invoke-Api -Method POST -Path "/sync/reindex" -Body @{ scope = "ids"; product_ids = @("gid://shopify/Product/123") } -Headers @{ "X-Admin-Token" = $ReindexAdminToken }
    Write-TestResult -Name "POST /sync/reindex correct token -> 200" -Success ($reindexGood.Ok -and $reindexGood.Data.accepted -eq $true)
}
else {
    Write-Host "[INFO] Skipping authenticated reindex tests (ReindexAdminToken not provided)." -ForegroundColor Yellow
}

# 9) Performance sanity (sequential search calls)
$perfFailures = 0
$perfStart = Get-Date
for ($i = 1; $i -le $PerfCount; $i++) {
    $perfResult = Invoke-Api -Method POST -Path "/search-products" -Body @{ query = "football"; filters = @{ in_stock_only = $true }; pagination = @{ limit = 3; offset = 0 } }
    if (-not $perfResult.Ok) {
        $perfFailures++
    }
}
$perfElapsedMs = [int]((Get-Date) - $perfStart).TotalMilliseconds
Write-TestResult -Name "Performance sanity: $PerfCount sequential searches with 0 failures" -Success ($perfFailures -eq 0) -Details "(failures=$perfFailures, elapsed_ms=$perfElapsedMs)"

Write-Host ""
Write-Host "Full Part 3 test summary: $passed passed, $failed failed." -ForegroundColor Cyan

if ($failed -gt 0) {
    exit 1
}

exit 0
