const readline = require("readline");
const { execSync } = require("child_process");
const https = require("https");
const path = require("path");

const DB_PATH = path.join(__dirname, "database.sqlite");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(question) {
  return new Promise((resolve) => rl.question(question, resolve));
}

function getGroupChats() {
  const output = execSync(
    `sqlite3 "${DB_PATH}" "SELECT id FROM chat WHERE id < 0;"`
  ).toString().trim();

  if (!output) return [];
  return output.split("\n").map((id) => id.trim()).filter(Boolean);
}

function parseMessageLink(link) {
  // Supports: https://t.me/channel/123 or https://t.me/c/123456/123
  const publicMatch = link.match(/https?:\/\/t\.me\/([a-zA-Z_]\w+)\/(\d+)/);
  if (publicMatch) {
    return { from_chat_id: `@${publicMatch[1]}`, message_id: parseInt(publicMatch[2]) };
  }

  const privateMatch = link.match(/https?:\/\/t\.me\/c\/(\d+)\/(\d+)/);
  if (privateMatch) {
    return { from_chat_id: `-100${privateMatch[1]}`, message_id: parseInt(privateMatch[2]) };
  }

  return null;
}

function copyMessage(botToken, chatId, fromChatId, messageId) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      chat_id: chatId,
      from_chat_id: fromChatId,
      message_id: messageId,
    });

    const options = {
      hostname: "api.telegram.org",
      path: `/bot${botToken}/copyMessage`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(data),
      },
    };

    const req = https.request(options, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        try {
          const json = JSON.parse(body);
          resolve(json);
        } catch {
          reject(new Error(`Invalid response: ${body}`));
        }
      });
    });

    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  console.log("\n📢 UnoBHAi Broadcast Tool\n");

  const botToken = await ask("🔑 Enter bot token: ");
  const messageLink = await ask("🔗 Enter message link (https://t.me/channel/message-id): ");

  const parsed = parseMessageLink(messageLink);
  if (!parsed) {
    console.log("❌ Invalid message link format!");
    rl.close();
    process.exit(1);
  }

  console.log(`\n📨 From: ${parsed.from_chat_id} | Message ID: ${parsed.message_id}`);

  const groups = getGroupChats();
  if (groups.length === 0) {
    console.log("❌ No group chats found in database!");
    rl.close();
    process.exit(1);
  }

  console.log(`📊 Found ${groups.length} group chats\n`);

  const confirm = await ask(`Send to all ${groups.length} groups? (yes/no): `);
  if (confirm.toLowerCase() !== "yes") {
    console.log("❌ Broadcast cancelled.");
    rl.close();
    process.exit(0);
  }

  console.log("\n🚀 Starting broadcast...\n");

  let success = 0;
  let failed = 0;
  const errors = [];

  for (let i = 0; i < groups.length; i++) {
    const chatId = groups[i];

    try {
      const result = await copyMessage(botToken, chatId, parsed.from_chat_id, parsed.message_id);

      if (result.ok) {
        success++;
      } else {
        failed++;
        errors.push({ chatId, error: result.description });
      }
    } catch (err) {
      failed++;
      errors.push({ chatId, error: err.message });
    }

    // Progress
    const total = i + 1;
    process.stdout.write(
      `\r📤 Progress: ${total}/${groups.length} | ✅ ${success} | ❌ ${failed}`
    );

    // Rate limit: ~25 messages/sec → 40ms delay
    await sleep(40);
  }

  console.log("\n\n✅ Broadcast finished!");
  console.log(`   ✅ Success: ${success}`);
  console.log(`   ❌ Failed: ${failed}`);

  if (errors.length > 0) {
    console.log("\n📋 Failed chats:");
    errors.slice(0, 20).forEach((e) => {
      console.log(`   ${e.chatId}: ${e.error}`);
    });
    if (errors.length > 20) {
      console.log(`   ... and ${errors.length - 20} more`);
    }
  }

  rl.close();
}

main();
