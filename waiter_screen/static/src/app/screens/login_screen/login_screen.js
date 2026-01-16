/** @odoo-module */

import { Component, useState } from "@odoo/owl";

export class WaiterLoginScreen extends Component {
    static template = "waiter_screen.LoginScreen";
    static props = {
        onLogin: Function,
    };

    setup() {
        this.state = useState({
            waiterName: "",
            waiterPin: "",
        });
    }

    handleSubmit(ev) {
        ev.preventDefault();

        if (!this.state.waiterName || !this.state.waiterPin) {
            alert("Please enter both name and PIN");
            return;
        }

        this.props.onLogin(this.state.waiterName, this.state.waiterPin);
    }

    handlePinInput(digit) {
        if (this.state.waiterPin.length < 4) {
            this.state.waiterPin += digit;
        }
    }

    handlePinClear() {
        this.state.waiterPin = "";
    }

    handlePinBackspace() {
        this.state.waiterPin = this.state.waiterPin.slice(0, -1);
    }
}
