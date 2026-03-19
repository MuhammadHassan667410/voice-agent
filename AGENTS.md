# CLAUDE.md — AI Shopify Assistant System

## 🧠 PROJECT OVERVIEW

This project is a production-grade AI-powered shopping assistant for Shopify.

The system enables:

* Semantic product search (RAG)
* Voice-based interaction (Vapi)
* Dynamic frontend control (no full page reloads)
* Cart operations (add/update)
* Real-time product sync from Shopify

---

## 🏗️ SYSTEM ARCHITECTURE

### Source of Truth

* Shopify (products, variants, inventory)

### Sync Layer

* n8n (webhooks)

### Backend API

* Node.js (Express) or FastAPI

### Database

* Supabase (Postgres + pgvector)

### AI Layer

* Vapi (voice agent)
* Embeddings (OpenAI or local)

### Frontend

* Shopify Liquid + Custom JS Widget

---

## 🔄 DATA FLOW

Shopify → n8n → Backend → Supabase
User → Widget → Backend → Vector Search → Supabase → Widget
Vapi → Backend → Widget → DOM Actions

---

## 📦 DATABASE DESIGN

### products table

* id (PK)
* title
* description
* price
* images (array)
* variants (JSON)
* tags
* inventory
* created_at
* updated_at

### product_embeddings table

* id
* product_id (FK)
* embedding (vector)
* metadata (JSON)

---

## 🧠 EMBEDDING STRATEGY

Embed only:

* title
* short description
* tags

Do NOT embed:

* images
* variants
* full JSON

---

## 🔁 SYNC LOGIC

### On Product Create

* insert into products
* generate embedding
* insert into product_embeddings

### On Product Update

* if text fields changed → re-embed
* else → update only structured data

### On Product Delete

* delete from both tables

---

## 🌐 BACKEND API DESIGN

### POST /search-products

* input: query
* generate embedding
* vector similarity search
* fetch full product data
* return structured response

### GET /product/:id

### POST /filter-products

* filter by price, tags, variants

---

## 🎤 VAPI INTEGRATION

Vapi acts as decision engine.

### Tools:

* search_products(query)
* open_product(product_id)
* add_to_cart(product_id, variant_id, quantity)
* update_cart(line_id, variant_id, quantity)
* show_cart()
* navigate(page)

### Rules:

* Vapi NEVER accesses DB directly
* Vapi NEVER controls DOM
* Vapi only returns structured actions

---

## 🖥️ FRONTEND WIDGET

### Responsibilities:

* render UI
* manage state
* execute actions
* control navigation
* interact with Shopify cart API

---

## 🧩 STATE MANAGEMENT

Per-user state (in browser only):

* products
* selectedProduct
* cart
* currentView

---

## 🔄 ACTION HANDLER

Central handler:

handleAction(action) {
switch(action.type) {
case "search_products":
case "open_product":
case "add_to_cart":
case "update_cart":
case "navigate":
}
}

---

## 🧭 NAVIGATION (NO RELOAD)

Use:

* fetch()
* history.pushState()
* DOM replacement

---

## 🛒 SHOPIFY CART API

* POST /cart/add.js
* POST /cart/update.js
* GET /cart.js

---

## 🔐 SECURITY RULES

* No API keys in frontend
* Backend is only gateway
* No global mutable state
* Per-user isolation

---

## 🚫 CONSTRAINTS

* Do NOT use Liquid for logic
* Do NOT use vector DB as primary DB
* Do NOT allow AI to modify products
* Do NOT reload entire page

---

## 🧪 TESTING REQUIREMENTS

* search returns correct products
* add to cart works
* cart updates correctly
* navigation works without reload
* multiple users do not interfere

---

## 📦 OUTPUT MODULES

1. Backend API
2. Supabase schema
3. n8n workflows
4. Vapi config
5. Frontend widget

---

## 🎯 FINAL SYSTEM BEHAVIOR

User can:

* search products
* view multiple items
* open product dynamically
* add to cart
* update cart
* navigate pages smoothly

All without full page reload.
