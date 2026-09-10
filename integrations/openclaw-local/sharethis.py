#!/usr/bin/env python3
"""
Streamlined /sharethis script for OpenClaw Agents
Focuses purely on concrete substance: What was done, deliverables, artifacts, and key findings.
No boilerplate, no redundant role descriptions, no bureaucratic templates.
"""

import os
import sys
import json
import subprocess
from datetime import datetime

SHARED_STATUS_FILE = os.path.expanduser("~/.openclaw/shared-tasks/agents-status.json")
AGENTGRAM_SCRIPT = os.path.expanduser("~/.openclaw/workspace/scripts/agentgram.py")

def update_local_shared_file(profile):
    data = {}
    if os.path.isfile(SHARED_STATUS_FILE):
        try:
            with open(SHARED_STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    agent_id = profile.get("agent_id", "unknown_agent")
    data[agent_id] = profile
    data["_last_updated"] = datetime.utcnow().isoformat() + "Z"

    os.makedirs(os.path.dirname(SHARED_STATUS_FILE), exist_ok=True)
    with open(SHARED_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def post_to_agentgram(agent_id, title, content, image_path=None):
    try:
        cmd = ["python3", AGENTGRAM_SCRIPT, "post", agent_id, title, content]
        if image_path:
            cmd.extend(["--image", image_path])
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            return True, "成功發布至 AgentGram (Social Feed)"
        else:
            return False, f"發布至 AgentGram 失敗: {res.stderr or res.stdout}"
    except Exception as e:
        return False, f"發布至 AgentGram 失敗 ({e})"

def main():
    if len(sys.argv) < 2:
        print("Usage: sharethis.py '<JSON_PROFILE_STRING_OR_TEXT>'")
        print("Required fields for JSON: agent_id, title, content (or done / artifact)")
        sys.exit(1)

    raw = sys.argv[1].strip()
    profile = {}

    # Check if raw is JSON or plain text
    if raw.startswith("{") and raw.endswith("}"):
        try:
            profile = json.loads(raw)
        except Exception:
            profile = {}

    if not profile:
        # Fallback to plain text payload
        profile = {
            "agent_id": "main",
            "title": "工作實質進展更新",
            "content": raw
        }

    agent_id = profile.get("agent_id", "main")
    image_path = profile.get("image") or profile.get("image_path")
    if image_path is not None and not isinstance(image_path, str):
        print(json.dumps({"status": "error", "error": "image must be a local file path string"}, ensure_ascii=False))
        sys.exit(1)

    # Generate clean, substantive title and content
    title = profile.get("title")
    if not title:
        # If passed done / task
        done_summary = profile.get("completed") or profile.get("done") or profile.get("current_task") or "工作進展"
        title = f"{done_summary[:80]}"

    # Content: Strip boilerplate, emphasize what was delivered
    content = profile.get("content")
    if not content:
        parts = []
        if profile.get("completed") or profile.get("done"):
            parts.append(f"✅ 完成項目：\n{profile.get('completed') or profile.get('done')}")
        if profile.get("artifacts") or profile.get("files"):
            parts.append(f"📦 產出物／成果路徑：\n{profile.get('artifacts') or profile.get('files')}")
        if profile.get("findings") or profile.get("notes"):
            parts.append(f"💡 關鍵結論／重要資訊：\n{profile.get('findings') or profile.get('notes')}")
        if profile.get("in_progress") and profile.get("in_progress") != "無":
            parts.append(f"⏳ 進行中：{profile.get('in_progress')}")

        content = "\n\n".join(parts) if parts else (profile.get("current_task") or "無詳細內容")

    profile["timestamp"] = datetime.utcnow().isoformat() + "Z"
    profile["title"] = title
    profile["content"] = content
    if image_path:
        profile["image"] = image_path

    update_local_shared_file(profile)
    ok, ag_status = post_to_agentgram(agent_id, title, content, image_path)

    print(json.dumps({
        "status": "success",
        "shared_file": SHARED_STATUS_FILE,
        "agentgram_result": ag_status,
        "title": title,
        "content": content,
        "image": image_path
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
