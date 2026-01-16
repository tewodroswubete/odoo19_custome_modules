/** @odoo-module */

import { Component, useState } from "@odoo/owl";

export class WaiterOrderScreen extends Component {
    static template = "waiter_screen.OrderScreen";
    static props = {
        waiter: Object,
        table: Object,
        order: Object,
        products: Array,
        categories: Array,
        onSendOrder: Function,
        onBack: Function,
    };

    setup() {
        this.state = useState({
            selectedCategory: null,
            searchQuery: "",
            orderLines: this.props.order.lines || [],
            notes: this.props.order.notes || "",
        });
    }

    get filteredProducts() {
        let products = this.props.products;

        // Filter by category
        if (this.state.selectedCategory) {
            products = products.filter((p) =>
                p.pos_categ_ids && p.pos_categ_ids.includes(this.state.selectedCategory)
            );
        }

        // Filter by search
        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            products = products.filter((p) => p.name.toLowerCase().includes(query));
        }

        return products;
    }

    get orderTotal() {
        return this.state.orderLines.reduce((sum, line) => {
            return sum + line.qty * line.price_unit;
        }, 0);
    }

    selectCategory(categoryId) {
        this.state.selectedCategory = this.state.selectedCategory === categoryId ? null : categoryId;
    }

    addProduct(product) {
        const existingLine = this.state.orderLines.find((l) => l.product_id === product.id);

        if (existingLine) {
            existingLine.qty += 1;
        } else {
            this.state.orderLines.push({
                product_id: product.id,
                product_name: product.name,
                qty: 1,
                price_unit: product.list_price,
                note: "",
            });
        }
    }

    updateQuantity(line, delta) {
        line.qty += delta;
        if (line.qty <= 0) {
            this.removeLine(line);
        }
    }

    removeLine(line) {
        const index = this.state.orderLines.indexOf(line);
        if (index > -1) {
            this.state.orderLines.splice(index, 1);
        }
    }

    handleSendOrder() {
        if (this.state.orderLines.length === 0) {
            alert("Please add items to the order");
            return;
        }

        const order = {
            table_id: this.props.table.id,
            lines: this.state.orderLines,
            notes: this.state.notes,
        };

        this.props.onSendOrder(order);
    }
}
