import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { getCurrentViewInfo } from "@ai/discuss/core/common/view_details";
import { session } from "@web/session";

console.log("🚀 AI Thread Model Patch Loading from ai/static/src/discuss/core/common/thread_model_patch.js");

patch(Thread.prototype, {
    async post(body, postData = {}, extraData = {}) {
        console.log("🟢 Thread.post called!", {
            channel_type: this.channel_type,
            this_ai_agent_id: this.ai_agent_id
        });

        const message = await super.post(body, postData, extraData);

        console.log("🟡 Message created:", message?.id, {
            message_thread_ai_agent_id: message?.thread?.ai_agent_id,
            this_channel_type: this.channel_type
        });

        const aiMember = this.channel_member_ids?.find(
            (member) => member.partner_id?.im_status == "agent"
        );

        // Check if this is an AI chat - use channel_type instead of ai_agent_id
        const isAIChat = this.channel_type === "ai_chat" || message?.thread?.channel_type === "ai_chat";

        // message could be undefined if it is a command, for example /help.
        if (message && isAIChat) {
            console.log("🟠 AI Chat detected! Triggering AI response...");

            try {
                if (aiMember) {
                    aiMember.isTyping = true;
                }

                console.log("🔴 Calling /ai/generate_response", {
                    mail_message_id: message.id,
                    channel_id: this.id
                });

                await rpc("/ai/generate_response", {
                    mail_message_id: message.id,
                    channel_id: this.id,
                    current_view_info: await getCurrentViewInfo(this.store.env.bus),
                    ai_session_identifier: session.ai_session_identifier,
                });

                console.log("✅ AI response triggered successfully!");

            } catch (error) {
                console.error("❌ AI trigger error:", error);
            } finally {
                if (aiMember) {
                    aiMember.isTyping = false;
                }
            }
        } else {
            console.log("⚪ Not an AI chat", {
                hasMessage: !!message,
                channel_type: this.channel_type,
                isAIChat: isAIChat
            });
        }
        return message;
    },
});

console.log("✅ AI Thread Model Patch Loaded Successfully!");
