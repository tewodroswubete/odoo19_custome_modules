/** @odoo-module */

import { Component, useState } from "@odoo/owl";

export class WaiterTableScreen extends Component {
    static template = "waiter_screen.TableScreen";
    static props = {
        waiter: Object,
        tables: Array,
        floors: Array,
        onSelectTable: Function,
        onLogout: Function,
        onRefresh: Function,
    };

    setup() {
        this.state = useState({
            selectedFloor: this.props.floors && this.props.floors.length > 0 ? this.props.floors[0].id : null,
        });
    }

    get currentFloor() {
        return this.props.floors.find((f) => f.id === this.state.selectedFloor);
    }

    get filteredTables() {
        return this.props.tables.filter((t) => {
            // floor_id can be [id, name] array or just id
            const floorId = Array.isArray(t.floor_id) ? t.floor_id[0] : t.floor_id;
            return floorId === this.state.selectedFloor;
        });
    }

    selectFloor(floorId) {
        this.state.selectedFloor = floorId;
    }

    getTableStatusClass(status) {
        const statusClasses = {
            available: "table-available",
            occupied: "table-occupied",
            preparing: "table-preparing",
            ready: "table-ready",
            payment: "table-payment",
        };
        return statusClasses[status] || "table-available";
    }

    getTableStatusLabel(status) {
        const labels = {
            available: "Available",
            occupied: "Occupied - Order Placed",
            preparing: "Food Preparing 🍳",
            ready: "Ready to Serve! ✅",
            payment: "Awaiting Payment 💳",
        };
        return labels[status] || "Available";
    }
}
