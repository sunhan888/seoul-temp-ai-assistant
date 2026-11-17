// ============================================================
// 서울 기온 AI 비서 — 프론트엔드 (바닐라 JS)
// 화면(HTML) ↔ 백엔드 API(fetch) 를 이어주는 역할
// ============================================================

// config.js 에서 넣어준 주소 (없으면 로컬 백엔드)
const API_BASE = (window.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

// 현재 보고 있는 대화 ID (null 이면 새 대화)
let currentConversationId = null;
// 데이터 수정 중인 항목 ID (null 이면 '추가' 모드)
let editingId = null;

const $ = (sel) => document.querySelector(sel);

// ---------- 공통: API 호출 함수 ----------
async function api(path, options = {}, timeoutMs = 70000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...options,
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      // FastAPI 오류 형식: {detail: "메시지"} 또는 {detail: [{msg: ...}]}
      const d = body.detail;
      const msg = Array.isArray(d) ? d.map((e) => e.msg).join(", ") : d || res.statusText;
      throw new Error(`${res.status} ${msg}`);
    }
    return body;
  } catch (err) {
    if (err.name === "AbortError") throw new Error("서버 응답 시간이 초과됐어요. 잠시 후 다시 시도해 주세요.");
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ---------- 1) 서버 상태 확인 (콜드스타트 대응) ----------
async function checkServer() {
  const badge = $("#server-status");
  const banner = $("#wake-banner");
  // 3초 안에 응답이 없으면 '깨우는 중' 안내를 띄움
  const slowTimer = setTimeout(() => banner.classList.remove("hidden"), 3000);
  try {
    await api("/health", {}, 90000);
    badge.textContent = "서버 연결됨";
    badge.className = "badge badge-ok";
    return true;
  } catch (e) {
    badge.textContent = "서버 연결 실패";
    badge.className = "badge badge-err";
    return false;
  } finally {
    clearTimeout(slowTimer);
    banner.classList.add("hidden");
  }
}

// ---------- 2) 데이터 요약 ----------
async function loadSummary() {
  const el = $("#summary");
  try {
    const s = await api("/api/data/summary");
    const m = s.metrics || {};
    const rows = [
      ["기간", s.period],
      ["개수", `${s.count}개`],
      ["평균", m.average != null ? `${m.average}℃` : "-"],
      ["최고", m.max != null ? `${m.max}℃ (${m.max_date})` : "-"],
      ["최저", m.min != null ? `${m.min}℃ (${m.min_date})` : "-"],
      ["추세", s.trend],
    ];
    el.innerHTML = "";
    for (const [k, v] of rows) {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = k;
      dd.textContent = v;
      el.append(dt, dd);
    }
  } catch (e) {
    el.innerHTML = `<dd class="muted">요약을 불러오지 못했어요 (${e.message})</dd>`;
  }
}

// ---------- 3) 채팅 ----------
function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text; // textContent: HTML로 해석하지 않아 안전
  $("#messages").append(div);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return div;
}

function resetChat() {
  currentConversationId = null;
  $("#messages").innerHTML = "";
  addMessage("assistant", "새 대화를 시작합니다. 무엇이 궁금하세요?");
  highlightConversation();
}

async function sendMessage(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  input.value = "";
  $("#send-btn").disabled = true;
  const loading = addMessage("loading", "");
  loading.innerHTML = '데이터를 살펴보는 중<span class="dots"></span>';

  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text, conversation_id: currentConversationId }),
    });
    loading.remove();
    addMessage("assistant", res.reply);
    currentConversationId = res.conversation_id; // 다음 질문부터 같은 대화로 이어짐
    loadConversations(); // 자동 저장된 대화를 목록에 반영
  } catch (e) {
    loading.remove();
    addMessage("error", `오류: ${e.message}`);
  } finally {
    $("#send-btn").disabled = false;
    input.focus();
  }
}

// ---------- 4) 대화 기록 ----------
async function loadConversations() {
  const ul = $("#conversation-list");
  try {
    const list = await api("/api/conversations");
    ul.innerHTML = "";
    if (list.length === 0) {
      ul.innerHTML = '<li class="muted">아직 저장된 대화가 없어요</li>';
      return;
    }
    for (const c of list) {
      const li = document.createElement("li");
      li.dataset.id = c.id;

      const open = document.createElement("button");
      open.className = "conv-open";
      open.innerHTML = `<span class="conv-title"></span><span class="conv-meta"></span>`;
      open.querySelector(".conv-title").textContent = c.title;
      open.querySelector(".conv-meta").textContent =
        `${c.message_count}개 메시지 · ${c.updated_at.slice(0, 16).replace("T", " ")}`;
      open.onclick = () => openConversation(c.id);

      const del = document.createElement("button");
      del.className = "conv-del";
      del.title = "대화 삭제";
      del.textContent = "✕";
      del.onclick = () => deleteConversation(c.id);

      li.append(open, del);
      ul.append(li);
    }
    highlightConversation();
  } catch (e) {
    ul.innerHTML = `<li class="muted">목록을 불러오지 못했어요 (${e.message})</li>`;
  }
}

function highlightConversation() {
  document.querySelectorAll("#conversation-list li").forEach((li) => {
    li.classList.toggle("active", li.dataset.id === currentConversationId);
  });
}

async function openConversation(id) {
  try {
    const conv = await api(`/api/conversations/${id}`);
    currentConversationId = conv.id;
    $("#messages").innerHTML = "";
    conv.messages.forEach((m) => addMessage(m.role, m.content));
    switchTab("chat");
    highlightConversation();
  } catch (e) {
    alert(`대화를 불러오지 못했어요: ${e.message}`);
  }
}

async function deleteConversation(id) {
  if (!confirm("이 대화를 삭제할까요?")) return;
  try {
    await api(`/api/conversations/${id}`, { method: "DELETE" });
    if (id === currentConversationId) resetChat();
    loadConversations();
  } catch (e) {
    alert(`삭제 실패: ${e.message}`);
  }
}

// ---------- 5) 데이터 관리 (CRUD) ----------
async function loadData(flashId = null) {
  const tbody = $("#data-tbody");
  try {
    const list = await api("/api/data");
    list.reverse(); // 최신 날짜가 위로
    tbody.innerHTML = "";
    for (const d of list) {
      const tr = document.createElement("tr");
      if (d.id === flashId) tr.className = "flash";
      tr.innerHTML = `<td></td><td></td><td></td>
        <td><button class="btn-link">수정</button><button class="btn-link danger">삭제</button></td>`;
      tr.children[0].textContent = d.date;
      tr.children[1].textContent = d.value;
      tr.children[2].textContent = d.memo;
      const [editBtn, delBtn] = tr.querySelectorAll("button");
      editBtn.onclick = () => startEdit(d);
      delBtn.onclick = () => deleteData(d);
      tbody.append(tr);
    }
    if (flashId) tbody.querySelector("tr.flash")?.scrollIntoView({ block: "center" });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" class="muted">목록을 불러오지 못했어요 (${e.message})</td></tr>`;
  }
}

function showResult(text) {
  $("#data-result").textContent = text;
}

function startEdit(d) {
  editingId = d.id;
  $("#f-date").value = d.date;
  $("#f-value").value = d.value;
  $("#f-memo").value = d.memo;
  $("#data-submit").textContent = "수정 저장";
  $("#data-cancel").classList.remove("hidden");
  showResult(`✏️ ${d.date} 데이터를 수정 중이에요`);
}

function cancelEdit() {
  editingId = null;
  $("#data-form").reset();
  $("#data-submit").textContent = "추가";
  $("#data-cancel").classList.add("hidden");
  showResult("");
}

async function submitData(event) {
  event.preventDefault();
  const payload = {
    date: $("#f-date").value,
    value: parseFloat($("#f-value").value),
    memo: $("#f-memo").value.trim(),
  };
  try {
    let saved;
    if (editingId) {
      saved = await api(`/api/data/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      showResult(`✅ 수정 완료: ${saved.date} → ${saved.value}℃`);
    } else {
      saved = await api("/api/data", { method: "POST", body: JSON.stringify(payload) });
      showResult(`✅ 추가 완료: ${saved.date} ${saved.value}℃`);
    }
    const msg = $("#data-result").textContent;
    cancelEdit();
    showResult(msg);
    await loadData(saved.id);
    loadSummary(); // 데이터가 바뀌면 요약도 갱신
  } catch (e) {
    showResult(`❌ 저장 실패: ${e.message}`);
  }
}

async function deleteData(d) {
  if (!confirm(`${d.date} (${d.value}℃) 데이터를 삭제할까요?`)) return;
  try {
    await api(`/api/data/${d.id}`, { method: "DELETE" });
    showResult(`🗑️ 삭제 완료: ${d.date}`);
    if (editingId === d.id) cancelEdit();
    loadData();
    loadSummary();
  } catch (e) {
    showResult(`❌ 삭제 실패: ${e.message}`);
  }
}

// ---------- 탭 전환 ----------
function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  $("#tab-chat").classList.toggle("hidden", name !== "chat");
  $("#tab-data").classList.toggle("hidden", name !== "data");
}

// ---------- 시작 ----------
document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => switchTab(t.dataset.tab)));
$("#chat-form").addEventListener("submit", sendMessage);
$("#data-form").addEventListener("submit", submitData);
$("#data-cancel").addEventListener("click", cancelEdit);
$("#new-chat-btn").addEventListener("click", resetChat);

(async function init() {
  const ok = await checkServer(); // 서버를 먼저 깨운 뒤
  if (!ok) return;
  loadSummary();                  // 나머지를 동시에 불러옴
  loadConversations();
  loadData();
})();
