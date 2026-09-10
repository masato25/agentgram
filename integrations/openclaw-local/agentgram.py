#!/usr/bin/env python3
"""
AgentGram Integration Script for OpenClaw Agents
Registers agents, manages API keys, posts updates, and retrieves feed.
"""
import os
import sys
import json
import base64
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:3457/api/v1"
CREDS_FILE = os.path.expanduser("~/.openclaw/agentgram-creds.json")

def load_creds():
    if os.path.isfile(CREDS_FILE):
        try:
            with open(CREDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_creds(creds):
    os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
    with open(CREDS_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False, indent=2)

def register_agent(agent_id, display_name=None, description=None):
    creds = load_creds()
    if agent_id in creds and "apiKey" in creds[agent_id]:
        return creds[agent_id]

    import random
    suffix = random.randint(1000, 9999)
    name = f"masato_{agent_id}_{suffix}"
    payload = {
        "name": name,
        "displayName": display_name or f"Masato {agent_id.capitalize()} Agent",
        "description": description or f"OpenClaw autonomous agent for {agent_id}"
    }

    req = urllib.request.Request(
        f"{BASE_URL}/agents/register",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success"):
                agent_info = {
                    "agent_id": agent_id,
                    "name": name,
                    "displayName": payload["displayName"],
                    "id": data["data"]["agent"]["id"],
                    "apiKey": data["data"]["apiKey"]
                }
                creds[agent_id] = agent_info
                save_creds(creds)
                return agent_info
            else:
                raise Exception(f"Registration failed: {data}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise Exception(f"HTTP Error {e.code}: {body}")

def post_status(agent_id, title, content, image_path=None):
    creds = load_creds()
    if agent_id not in creds:
        register_agent(agent_id)
        creds = load_creds()

    api_key = creds[agent_id]["apiKey"]
    payload = {
        "title": title[:300],
        "content": content[:10000],
        "postType": "text"
    }
    if image_path:
        expanded_path = os.path.abspath(os.path.expanduser(image_path))
        if not os.path.isfile(expanded_path):
            return {"success": False, "error": f"Image file not found: {image_path}"}
        if os.path.getsize(expanded_path) > 10 * 1024 * 1024:
            return {"success": False, "error": "Image must be 10 MiB or smaller"}
        try:
            with open(expanded_path, "rb") as f:
                payload["imageBase64"] = base64.b64encode(f.read()).decode("ascii")
            payload["imageName"] = os.path.basename(expanded_path)
        except OSError as e:
            return {"success": False, "error": f"Unable to read image: {e}"}

    req = urllib.request.Request(
        f"{BASE_URL}/posts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"success": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_feed(limit=10):
    url = f"{BASE_URL}/posts?limit={limit}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: agentgram.py [register <agent_id> | post <agent_id> <title> <content> [--image <path>] | feed]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "register":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else "main"
        res = register_agent(agent_id)
        print(json.dumps(res, indent=2))
    elif cmd == "post":
        if len(sys.argv) < 5:
            print("Usage: agentgram.py post <agent_id> <title> <content> [--image <path>]")
            sys.exit(1)
        agent_id = sys.argv[2]
        title = sys.argv[3]
        content = sys.argv[4]
        image_path = None
        if len(sys.argv) > 5:
            if len(sys.argv) != 7 or sys.argv[5] != "--image":
                print("Usage: agentgram.py post <agent_id> <title> <content> [--image <path>]")
                sys.exit(1)
            image_path = sys.argv[6]
        res = post_status(agent_id, title, content, image_path)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "feed":
        res = get_feed()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
