import { Store } from "@mail/core/common/store_service";
import { patch } from "@web/core/utils/patch";

// Patch the Store to add Thread as an alias for "mail.thread"
// This maintains compatibility with AI module code that uses mailStore.Thread
patch(Store.prototype, {
    setup() {
        super.setup(...arguments);
        // Add Thread as a getter that returns the "mail.thread" model
        Object.defineProperty(this, "Thread", {
            get() {
                return this["mail.thread"];
            },
            configurable: true,
            enumerable: false,
        });
    },
});
