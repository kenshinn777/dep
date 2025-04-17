import asyncio
import random
import json
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest

# ========== DAFTAR AKUN ==========
accounts = [
    {
        'api_id': 24592475,
        'api_hash': '24a08e508e24d4e32fd40551ab71a261',
        'phone': '+62859218613748',
        'is_active': True
    }
]

# ========== LINK PESAN ==========
link = 'https://t.me/xinndb1/3'
fallback_link = 'https://t.me/dbgacor777/14'

# ========== LOAD GRUP ==========
def load_groups_from_file():
    try:
        with open("groups.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Gagal membaca groups.json: {e}")
        return {}

# ========== CEK KEANGGOTAAN ==========
async def is_member_of_group(client, group_username):
    try:
        entity = await client.get_entity(group_username)
        await client.get_participants(entity)
        return True
    except:
        return False

# ========== AMBIL PESAN DARI LINK ==========
async def get_message_from_link(client, link):
    try:
        parts = link.strip().split('/')
        username = parts[-2]
        message_id = int(parts[-1])
        entity = await client.get_entity(username)
        msg = await client.get_messages(entity, ids=message_id)
        return msg
    except Exception as e:
        print(f"❌ Gagal ambil pesan dari {link}: {e}")
        return None

# ========== FORWARD PESAN ==========
async def forward_from_link_for_account(account, link):
    if not account['is_active']:
        print(f"❌ Akun {account['phone']} nonaktif. Skip.\n")
        return

    client = TelegramClient('session_' + account['phone'], account['api_id'], account['api_hash'])
    await client.start(account['phone'])
    await asyncio.sleep(random.randint(3, 7))

    try:
        msg = await get_message_from_link(client, link)
        if not msg:
            print(f"❌ ({account['phone']}) Tidak bisa ambil pesan utama.")
            return

        print(f"\n📨 ({account['phone']}) Isi Pesan: {(msg.text or '[media only]')[:100]}...\n")

        group_data = load_groups_from_file()
        group_links = group_data.get(account['phone'], [])

        while True:
            available_groups = group_links.copy()
            random.shuffle(available_groups)

            for group_link in available_groups:
                group_username = group_link.split("/")[-1]

                try:
                    if not await is_member_of_group(client, group_username):
                        try:
                            await client(JoinChannelRequest(group_username))
                            print(f"✅ Berhasil join {group_username}")
                            await asyncio.sleep(3)
                        except Exception as e:
                            print(f"❌ Gagal join {group_username}: {e}")
                            continue

                    entity = await client.get_entity(group_username)
                    await client.forward_messages(entity, msg)
                    print(f"✅ ({account['phone']}) Forward ke {group_link}")
                except Exception as e:
                    if 'FloodWait' in e.__class__.__name__:
                        wait_time = getattr(e, 'seconds', 60)
                        print(f"⏳ FloodWait! Tunggu {wait_time} detik...")
                        await asyncio.sleep(wait_time)
                        continue
                    elif 'CHAT_SEND_PHOTOS_FORBIDDEN' in str(e):
                        print(f"⚠️ Gagal kirim karena media, ambil pesan fallback...")
                        fallback_msg = await get_message_from_link(client, fallback_link)
                        if fallback_msg:
                            try:
                                await client.forward_messages(entity, fallback_msg)
                                print(f"🔁 ({account['phone']}) Forward ulang fallback ke {group_link}")
                            except Exception as ef:
                                print(f"❌ Gagal kirim fallback ke {group_link}: {ef}")
                        else:
                            print("❌ Fallback message tidak ditemukan.")
                    else:
                        print(f"⚠️ Gagal forward ke {group_link}: {e}")
                    continue

            delay = random.randint(120, 180)
            print(f"⏳ Delay {delay} detik sebelum ulangi forward untuk {account['phone']}")
            await asyncio.sleep(delay)

    except Exception as e:
        print(f"❌ ERROR umum akun {account['phone']}: {e}")

# ========== MAIN ==========
async def main():
    print("=== 🚀 Multi-Akun Telegram Forwarder Tanpa Rotasi Dimulai ===\n")

    tasks = []
    for acc in accounts:
        if acc['is_active']:
            tasks.append(asyncio.create_task(forward_from_link_for_account(acc, link)))

    await asyncio.gather(*tasks)

# ========== EKSEKUSI ==========
if __name__ == '__main__':
    asyncio.run(main())
