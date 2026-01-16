import { registry } from "@web/core/registry";

async function initChat(env, action) {
    const mailStore = env.services["mail.store"];
    if (!mailStore) {
        throw new Error("Mail store service not available");
    }

    const thread = await mailStore.Thread.getOrFetch({
        model: "discuss.channel",
        id: Number(action.params.channelId),
    });
    if (!thread) {
        throw new Error("Thread not found");
    }
    thread.open({ focus: true });
    await thread.isLoadedDeferred;
    if (action.params.user_prompt && thread.status !== "loading") {
        await thread.post(action.params.user_prompt);
    }
}

registry.category("actions").add("agent_chat_action", initChat);
