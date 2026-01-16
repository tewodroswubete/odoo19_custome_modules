/** @odoo-module */

import { Component, useState } from "@odoo/owl";

export class WaiterPaymentScreen extends Component {
    static template = "waiter_screen.PaymentScreen";
    static props = {
        waiter: Object,
        table: Object,
        order: Object,
        paymentMethods: Array,
        onPayment: Function,
        onBack: Function,
    };

    setup() {
        this.state = useState({
            selectedPaymentMethod: this.props.paymentMethods.length > 0 ? this.props.paymentMethods[0].id : null,
            amountReceived: this.getOrderTotal(),
        });
    }

    getOrderTotal() {
        // If order has amount_total (existing order), use it
        if (this.props.order.amount_total !== undefined) {
            return this.props.order.amount_total;
        }
        // Otherwise calculate from lines (new order)
        return this.props.order.lines.reduce((sum, line) => {
            return sum + (line.qty * line.price_unit);
        }, 0);
    }

    get change() {
        return Math.max(0, this.state.amountReceived - this.getOrderTotal());
    }

    selectPaymentMethod(methodId) {
        this.state.selectedPaymentMethod = methodId;
    }

    handlePayment() {
        if (!this.state.selectedPaymentMethod) {
            alert("Please select a payment method");
            return;
        }

        if (this.state.amountReceived < this.getOrderTotal()) {
            alert("Amount received is less than order total");
            return;
        }

        const paymentData = {
            payment_method_id: this.state.selectedPaymentMethod,
            amount: this.state.amountReceived,
            payment_name: "Payment",
        };

        this.props.onPayment(paymentData);
    }

    addAmount(amount) {
        this.state.amountReceived += amount;
    }

    setExactAmount() {
        this.state.amountReceived = this.getOrderTotal();
    }
}
