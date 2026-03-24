param(
    [string]$BaseUrl = "https://muhammadhassan.tech",
    [string]$ShopDomain = "pmcvp2-tv.myshopify.com"
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

function Invoke-Api {
    param(
        [ValidateSet("GET", "POST", "DELETE", "PUT", "PATCH")]
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )

    $uri = "$BaseUrl$Path"

    try {
        if ($null -ne $Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 20
            $response = Invoke-RestMethod -Uri $uri -Method $Method -Headers $Headers -ContentType "application/json" -Body $jsonBody
        }
        else {
            $response = Invoke-RestMethod -Uri $uri -Method $Method -Headers $Headers
        }

        return [pscustomobject]@{
            Ok     = $true
            Status = 200
            Data   = $response
            Raw    = $null
        }
    }
    catch {
        $status = -1
        $raw = $null
        $data = $null

        if ($_.Exception.Response) {
            try {
                $status = [int]$_.Exception.Response.StatusCode.value__
            }
            catch {
                $status = -1
            }

            try {
                $stream = $_.Exception.Response.GetResponseStream()
                if ($stream) {
                    $reader = New-Object System.IO.StreamReader($stream)
                    $raw = $reader.ReadToEnd()
                    $reader.Close()
                    if ($raw) {
                        try {
                            $data = $raw | ConvertFrom-Json -ErrorAction Stop
                        }
                        catch {
                            $data = $null
                        }
                    }
                }
            }
            catch {
            }
        }

        return [pscustomobject]@{
            Ok     = $false
            Status = $status
            Data   = $data
            Raw    = $raw
        }
    }
}

Write-Host "Running Part 3 API tests against $BaseUrl" -ForegroundColor Cyan

# Test 1: Health
$health = Invoke-Api -Method GET -Path "/health"
$healthPass = $health.Ok -and $health.Data.status -eq "ok" -and $health.Data.trace_id
Write-TestResult -Name "GET /health" -Success $healthPass

# Test 2: Filter products
$filterBody = @{
    filters = @{ in_stock_only = $true }
    sort = @{ field = "updated_at"; order = "desc" }
    pagination = @{ limit = 5; offset = 0 }
}
$filter = Invoke-Api -Method POST -Path "/filter-products" -Body $filterBody
$filterPass = $filter.Ok -and $null -ne $filter.Data.items -and $null -ne $filter.Data.page -and $filter.Data.page.limit -eq 5
Write-TestResult -Name "POST /filter-products" -Success $filterPass

# Test 3: Search products
$searchBody = @{
    query = "football"
    filters = @{ in_stock_only = $true }
    pagination = @{ limit = 5; offset = 0 }
}
$search = Invoke-Api -Method POST -Path "/search-products" -Body $searchBody
$searchPass = $search.Ok -and $null -ne $search.Data.items -and $null -ne $search.Data.page -and $search.Data.page.limit -eq 5
Write-TestResult -Name "POST /search-products" -Success $searchPass

# Test 4-8: Sync lifecycle tests
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
            @{
                id = $variantId
                title = "Default"
                price = "29.99"
                inventory_quantity = 12
            }
        )
        images = @(
            @{ src = "https://example.com/ball.jpg" }
        )
    }
}

$created = Invoke-Api -Method POST -Path "/sync/shopify/product-created" -Body $createdPayload
$createdPass = $created.Ok -and $created.Data.status -eq "processed" -and $created.Data.embedding_action -eq "created"
Write-TestResult -Name "POST /sync/shopify/product-created" -Success $createdPass

# idempotency check (same envelope)
$createdDup = Invoke-Api -Method POST -Path "/sync/shopify/product-created" -Body $createdPayload
$createdDupPass = $createdDup.Ok -and $createdDup.Data.status -eq "skipped" -and $createdDup.Data.embedding_action -eq "skipped"
Write-TestResult -Name "Idempotency: duplicate create skipped" -Success $createdDupPass

# price-only update should skip re-embed
$updatedPriceOnly = $createdPayload.PSObject.Copy()
$updatedPriceOnly.event_id = "evt-update-price-$productId"
$updatedPriceOnly.occurred_at = (Get-Date).ToUniversalTime().AddSeconds(1).ToString("o")
$updatedPriceOnly.payload = $createdPayload.payload.PSObject.Copy()
$updatedPriceOnly.payload.variants = @(
    @{
        id = $variantId
        title = "Default"
        price = "31.99"
        inventory_quantity = 9
    }
)

$updatePrice = Invoke-Api -Method POST -Path "/sync/shopify/product-updated" -Body $updatedPriceOnly
$updatePricePass = $updatePrice.Ok -and $updatePrice.Data.status -eq "processed" -and $updatePrice.Data.embedding_action -eq "skipped"
Write-TestResult -Name "POST /sync/shopify/product-updated (price only)" -Success $updatePricePass

# text update should re-embed
$updatedText = $createdPayload.PSObject.Copy()
$updatedText.event_id = "evt-update-text-$productId"
$updatedText.occurred_at = (Get-Date).ToUniversalTime().AddSeconds(2).ToString("o")
$updatedText.payload = $createdPayload.payload.PSObject.Copy()
$updatedText.payload.title = "Test Ball Updated $productId"
$updatedText.payload.tags = "football,match,premium"
$updatedText.payload.body_html = "<p>Updated match ball description</p>"

$updateText = Invoke-Api -Method POST -Path "/sync/shopify/product-updated" -Body $updatedText
$updateTextPass = $updateText.Ok -and $updateText.Data.status -eq "processed" -and $updateText.Data.embedding_action -eq "updated"
Write-TestResult -Name "POST /sync/shopify/product-updated (text changed)" -Success $updateTextPass

# delete
$deleteBody = @{
    shop_domain = $ShopDomain
    event_id = "evt-delete-$productId"
    occurred_at = (Get-Date).ToUniversalTime().AddSeconds(3).ToString("o")
    payload = @{ id = $productId }
}

$deleted = Invoke-Api -Method POST -Path "/sync/shopify/product-deleted" -Body $deleteBody
$deletedPass = $deleted.Ok -and $deleted.Data.status -eq "processed" -and $deleted.Data.embedding_action -eq "deleted"
Write-TestResult -Name "POST /sync/shopify/product-deleted" -Success $deletedPass

# Test 9: Get deleted product should be 404
$gid = "gid://shopify/Product/$productId"
$getDeleted = Invoke-Api -Method GET -Path "/product/$gid"
$getDeletedPass = (-not $getDeleted.Ok) -and $getDeleted.Status -eq 404
Write-TestResult -Name "GET /product/{id} after delete returns 404" -Success $getDeletedPass

# Test 10: Validation error test
$badSearch = Invoke-Api -Method POST -Path "/search-products" -Body @{ query = "" }
$badSearchPass = (-not $badSearch.Ok) -and $badSearch.Status -eq 400
Write-TestResult -Name "Validation: empty query returns 400" -Success $badSearchPass

# Test 11: Reindex auth/config guard
$reindex = Invoke-Api -Method POST -Path "/sync/reindex" -Body @{ scope = "all" }
$reindexPass = (-not $reindex.Ok) -and ($reindex.Status -eq 403 -or $reindex.Status -eq 500)
Write-TestResult -Name "POST /sync/reindex guard (403 or 500)" -Success $reindexPass

Write-Host ""
Write-Host "Part 3 test summary: $passed passed, $failed failed." -ForegroundColor Cyan

if ($failed -gt 0) {
    exit 1
}

exit 0
