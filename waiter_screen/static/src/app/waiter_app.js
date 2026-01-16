/** @odoo-module */

import { Component, useState, onMounted, whenReady } from "@odoo/owl";
import { mountComponent } from "@web/env";
import { WaiterLoginScreen } from "./screens/login_screen/login_screen";
import { WaiterTableScreen } from "./screens/table_screen/table_screen";
import { WaiterOrderScreen } from "./screens/order_screen/order_screen";
import { WaiterPaymentScreen } from "./screens/payment_screen/payment_screen";

export class WaiterApp extends Component {
    static template = "waiter_screen.WaiterApp";
    static components = {
        WaiterLoginScreen,
        WaiterTableScreen,
        WaiterOrderScreen,
        WaiterPaymentScreen,
    };

    setup() {
        this.state = useState({
            currentScreen: "login",
            waiter: null,
            session: null,
            selectedTable: null,
            currentOrder: null,
            tables: [],
            floors: [],
            products: [],
            categories: [],
            paymentMethods: [],
        });

        onMounted(() => {
            console.log("Waiter App Mounted!");
        });
    }

    async handleLogin(waiterName, waiterPin) {
        console.log("Login attempt:", waiterName, waiterPin);

        try {
            const response = await fetch('/pos/waiter/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        login: waiterName,
                        pin: waiterPin,
                    },
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            console.log("Login response (raw):", responseText);

            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse login response as JSON:", e);
                console.error("Response was:", responseText.substring(0, 500));
                alert("Login failed: Server returned an error. Check console for details.");
                return;
            }

            console.log("Login response:", data);

            if (data.result && data.result.success) {
                this.state.waiter = data.result.waiter;
                this.state.session = data.result.session;

                // Load data from login response
                this.state.tables = data.result.tables || [];
                this.state.floors = data.result.floors || [];
                this.state.products = data.result.products || [];
                this.state.categories = data.result.categories || [];
                this.state.paymentMethods = data.result.payment_methods || [];

                console.log("Login successful!");
                console.log("Tables loaded:", this.state.tables.length);
                console.log("Floors loaded:", this.state.floors.length);
                console.log("Products loaded:", this.state.products.length);

                // Navigate to tables
                this.state.currentScreen = "tables";
            } else {
                alert(data.result?.error || "Login failed");
                if (data.result?.traceback) {
                    console.error("Traceback:", data.result.traceback);
                }
            }
        } catch (error) {
            console.error("Login error:", error);
            alert("Login error: " + error.message);
        }
    }

    async loadWaiterData() {
        try {
            const response = await fetch('/pos/waiter/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {},
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse waiter data response as JSON:", e);
                console.error("Response was:", responseText.substring(0, 500));
                return;
            }

            if (data.result && !data.result.error) {
                this.state.tables = data.result.tables || [];
                this.state.floors = data.result.floors || [];
                this.state.products = data.result.products || [];
                this.state.categories = data.result.categories || [];
                this.state.paymentMethods = data.result.payment_methods || [];
                console.log("Data loaded:", data.result);
            }
        } catch (error) {
            console.error("Failed to load data:", error);
        }
    }

    async refreshTables() {
        console.log("Refreshing tables...");

        try {
            const response = await fetch('/pos/waiter/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {},
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse refresh data:", e);
                return;
            }

            if (data.result && !data.result.error) {
                this.state.tables = data.result.tables || [];
                this.state.floors = data.result.floors || [];
                this.state.products = data.result.products || [];
                this.state.categories = data.result.categories || [];
                this.state.paymentMethods = data.result.payment_methods || [];
                console.log("Tables refreshed:", this.state.tables.length);
            }
        } catch (error) {
            console.error("Failed to refresh tables:", error);
        }
    }

    async handleSelectTable(table) {
        console.log("Selected table:", table);
        this.state.selectedTable = table;

        // If table is occupied, ask what to do
        if (table.status && table.status !== 'available') {
            const action = confirm(
                `Table ${table.table_number} has an existing order.\n\n` +
                `Click OK to ADD MORE ITEMS to the order\n` +
                `Click CANCEL to PROCESS PAYMENT`
            );

            if (action) {
                // User chose to add more items
                await this.loadTableOrderForEditing(table.id);
            } else {
                // User chose to process payment
                await this.loadTableOrder(table.id);
            }
        } else {
            // New order for available table
            this.state.currentOrder = {
                table_id: table.id,
                lines: [],
                notes: "",
            };
            this.state.currentScreen = "order";
        }
    }

    async loadTableOrder(tableId) {
        console.log("Loading order for payment:", tableId);

        try {
            const response = await fetch('/pos/waiter/get_table_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        table_id: tableId,
                    },
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse order data:", e);
                alert("Error loading table order");
                return;
            }

            if (data.result && data.result.success) {
                // Load existing order for payment
                this.state.currentOrder = data.result.order;
                // Go directly to payment screen
                this.state.currentScreen = "payment";
            } else {
                alert("Error: " + (data.result?.error || "Could not load order"));
            }
        } catch (error) {
            console.error("Error loading table order:", error);
            alert("Error loading order: " + error.message);
        }
    }

    async loadTableOrderForEditing(tableId) {
        console.log("Loading order for editing:", tableId);

        try {
            const response = await fetch('/pos/waiter/get_table_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        table_id: tableId,
                    },
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse order data:", e);
                alert("Error loading table order");
                return;
            }

            if (data.result && data.result.success) {
                // Load existing order for editing (adding items)
                this.state.currentOrder = {
                    id: data.result.order.id,
                    name: data.result.order.name,
                    table_id: data.result.order.table_id,
                    lines: data.result.order.lines,
                    isExistingOrder: true,  // Flag to know this is an existing order
                };
                // Go to order screen to add more items
                this.state.currentScreen = "order";
            } else {
                alert("Error: " + (data.result?.error || "Could not load order"));
            }
        } catch (error) {
            console.error("Error loading table order for editing:", error);
            alert("Error loading order: " + error.message);
        }
    }

    handleBackToTables() {
        this.state.selectedTable = null;
        this.state.currentOrder = null;
        this.state.currentScreen = "tables";
        this.refreshTables();
    }

    async handleSendOrder(order) {
        console.log("Sending order:", order);

        // Check if this is updating an existing order or creating a new one
        const isUpdate = order.isExistingOrder || order.id;
        const endpoint = isUpdate ? '/pos/waiter/add_items_to_order' : '/pos/waiter/create_order';

        try {
            const params = isUpdate ? {
                order_id: order.id,
                lines: order.lines,
            } : {
                table_id: order.table_id,
                lines: order.lines,
                notes: order.notes || '',
            };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: params,
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse order response as JSON:", e);
                console.error("Response was:", responseText.substring(0, 500));
                alert("Failed to send order: Server returned an error. Check console for details.");
                return;
            }

            console.log("Order response:", data);

            if (data.result && data.result.success) {
                // Show success message
                const message = isUpdate
                    ? `✅ Additional items added to order ${data.result.order_name}!\nNew Total: $${data.result.amount_total.toFixed(2)}\n\nItems sent to kitchen!`
                    : `✅ Order ${data.result.order_name} sent to kitchen!\nTotal: $${data.result.amount_total.toFixed(2)}\n\nTable is now occupied. You can take orders from other tables.`;

                alert(message);

                // Clear current order and table
                this.state.currentOrder = null;
                this.state.selectedTable = null;

                // Refresh table list to show updated status
                await this.refreshTables();

                // Navigate back to table selection
                this.state.currentScreen = "tables";
            } else {
                alert("❌ Failed to create order: " + (data.result?.error || "Unknown error"));
                if (data.result?.traceback) {
                    console.error("Traceback:", data.result.traceback);
                }
            }
        } catch (error) {
            console.error("Error sending order:", error);
            alert("❌ Error sending order: " + error.message);
        }
    }

    async handlePayment(paymentData) {
        console.log("Processing payment:", paymentData);

        try {
            const response = await fetch('/pos/waiter/process_payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        order_id: this.state.currentOrder.id,
                        payment_method_id: paymentData.payment_method_id,
                        amount: paymentData.amount,
                    },
                    id: new Date().getTime(),
                }),
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error("Failed to parse payment response:", e);
                alert("Error processing payment");
                return;
            }

            if (data.result && data.result.success) {
                alert(`✅ Payment Received!\nOrder: ${data.result.order_name}\nAmount: $${paymentData.amount.toFixed(2)}\n\nTable is now available for new customers.`);

                // Refresh tables and return to table selection
                await this.refreshTables();
                this.handleBackToTables();
            } else {
                alert("❌ Payment failed: " + (data.result?.error || "Unknown error"));
                if (data.result?.traceback) {
                    console.error("Traceback:", data.result.traceback);
                }
            }
        } catch (error) {
            console.error("Error processing payment:", error);
            alert("Error processing payment: " + error.message);
        }
    }

    async handleLogout() {
        this.state.waiter = null;
        this.state.session = null;
        this.state.currentScreen = "login";
    }
}

// Mount the app when page loads
whenReady(() => {
    console.log("Mounting Waiter App...");
    const target = document.getElementById("waiter-app-root");

    if (target) {
        mountComponent(WaiterApp, target);
        console.log("Waiter App mounted successfully!");
    } else {
        console.error("Could not find #waiter-app-root element!");
    }
});
