"use strict";

const scanner = new Html5Qrcode("reader");
const networkStatus = document.getElementById("network-status");
const networkLabel = document.getElementById("network-label");
const cameraNote = document.getElementById("camera-note");
const startButton = document.getElementById("start-button");
const stopButton = document.getElementById("stop-button");
const result = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const resultMessage = document.getElementById("result-message");
const LUNCHES_KEY = "lanches_hoje";
const LUNCH_DATE_KEY = "lanches_hoje_data";
const LOCKOUT_MS = 3000;

let scannerRunning = false;
let processingScan = false;
let lastScanAt = 0;
let flashTimeout;
let audioContext;

function updateNetworkStatus() {
  const online = navigator.onLine;
  networkStatus.classList.toggle("online", online);
  networkStatus.classList.toggle("offline", !online);
  networkLabel.textContent = online
    ? "Online · validação no servidor"
    : "Offline · validação neste dispositivo";
}

function localDateString() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function getTodayLunches() {
  const today = localDateString();
  if (localStorage.getItem(LUNCH_DATE_KEY) !== today) {
    localStorage.setItem(LUNCHES_KEY, JSON.stringify([]));
    localStorage.setItem(LUNCH_DATE_KEY, today);
    return [];
  }

  const saved = localStorage.getItem(LUNCHES_KEY);
  const lunches = saved === null ? [] : JSON.parse(saved);
  if (!Array.isArray(lunches) || lunches.some((id) => typeof id !== "string")) {
    throw new Error("A lista offline de hoje está inválida. Limpe os dados locais para continuar.");
  }
  return lunches;
}

function saveLunchLocally(idAluno) {
  const lunches = getTodayLunches();
  if (!lunches.includes(idAluno)) {
    lunches.push(idAluno);
    localStorage.setItem(LUNCHES_KEY, JSON.stringify(lunches));
  }
}

function playTone(frequency, durationMs, waveform) {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      throw new Error("Este navegador não oferece suporte ao áudio.");
    }
    audioContext = audioContext || new AudioContextClass();
    if (audioContext.state === "suspended") {
      audioContext.resume();
    }

    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    const startAt = audioContext.currentTime;
    const endAt = startAt + durationMs / 1000;
    oscillator.type = waveform;
    oscillator.frequency.setValueAtTime(frequency, startAt);
    gain.gain.setValueAtTime(0.0001, startAt);
    gain.gain.exponentialRampToValueAtTime(0.22, startAt + 0.025);
    gain.gain.setTargetAtTime(0.0001, endAt - 0.08, 0.035);
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start(startAt);
    oscillator.stop(endAt);
  } catch (error) {
    console.error("Não foi possível reproduzir o som de confirmação.", error);
  }
}

function showResult(type, title, message, sound) {
  result.className = `result visible ${type}`;
  resultTitle.textContent = title;
  resultMessage.textContent = message;

  document.body.classList.remove("flash-success", "flash-blocked");
  window.clearTimeout(flashTimeout);
  if (type === "success" || type === "blocked") {
    const flashClass = type === "success" ? "flash-success" : "flash-blocked";
    document.body.classList.add(flashClass);
    flashTimeout = window.setTimeout(() => {
      document.body.classList.remove(flashClass);
    }, 900);
  }

  if (sound === "success") playTone(880, 180, "sine");
  if (sound === "blocked") playTone(165, 1200, "triangle");
}

function parseStudentId(decodedText) {
  const rawId = decodedText.trim();
  if (!rawId) return "";
  try {
    const parsed = JSON.parse(rawId);
    if (parsed && typeof parsed === "object" && "id_aluno" in parsed) {
      return String(parsed.id_aluno).trim();
    }
  } catch {
    // QR Codes with a plain-text ID are also supported.
  }
  return rawId;
}

async function handleScan(decodedText) {
  const now = Date.now();
  if (processingScan || now - lastScanAt < LOCKOUT_MS) return;
  lastScanAt = now;
  processingScan = true;

  try {
    const idAluno = parseStudentId(decodedText);
    if (!idAluno) {
      showResult("error", "QR Code inválido", "O código não contém um ID de aluno válido.");
      return;
    }

    if (!navigator.onLine) {
      const lunches = getTodayLunches();
      if (lunches.includes(idAluno)) {
        showResult(
          "blocked",
          "LANCHE JÁ RETIRADO",
          `O aluno ${idAluno} já foi registrado hoje neste dispositivo.`,
          "blocked"
        );
        return;
      }

      saveLunchLocally(idAluno);
      showResult(
        "success",
        "LANCHE LIBERADO",
        `Aluno ${idAluno} registrado offline neste dispositivo.`,
        "success"
      );
      return;
    }

    const response = await fetch("/verificar_qr", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_aluno: idAluno })
    });
    const data = await response.json();

    if (data.status === "sucesso") {
      let cacheWarning = "";
      try {
        saveLunchLocally(idAluno);
      } catch (error) {
        console.error("Não foi possível atualizar a lista offline.", error);
        cacheWarning = " A cópia offline não pôde ser atualizada.";
      }
      showResult("success", "LANCHE LIBERADO", `${data.mensagem}${cacheWarning}`, "success");
    } else if (data.status === "bloqueado") {
      try {
        saveLunchLocally(idAluno);
      } catch (error) {
        console.error("Não foi possível atualizar a lista offline.", error);
      }
      showResult("blocked", "LANCHE JÁ RETIRADO", data.mensagem, "blocked");
    } else {
      showResult("error", "Não foi possível validar", data.mensagem || "Tente novamente.");
    }
  } catch (error) {
    console.error("Falha ao verificar o QR Code.", error);
    showResult(
      "error",
      "Falha na verificação",
      "Não foi possível consultar o servidor ou a lista offline. Verifique a conexão e tente novamente."
    );
  } finally {
    window.setTimeout(() => {
      processingScan = false;
    }, Math.max(0, LOCKOUT_MS - (Date.now() - lastScanAt)));
  }
}

async function startScanner() {
  startButton.disabled = true;
  cameraNote.textContent = "Solicitando acesso à câmera…";
  try {
    await scanner.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 }, aspectRatio: 1 },
      handleScan,
      () => {}
    );
    scannerRunning = true;
    stopButton.disabled = false;
    cameraNote.textContent = "Aponte a câmera traseira para o QR Code do aluno.";
  } catch (error) {
    console.error("Não foi possível iniciar a câmera.", error);
    cameraNote.textContent = "Não foi possível abrir a câmera. Verifique a permissão do navegador.";
    showResult(
      "error",
      "Câmera indisponível",
      "Permita o acesso à câmera e tente novamente. Em celulares, use uma conexão HTTPS."
    );
  } finally {
    startButton.disabled = scannerRunning;
  }
}

async function stopScanner() {
  if (!scannerRunning) return;
  stopButton.disabled = true;
  try {
    await scanner.stop();
    scannerRunning = false;
    cameraNote.textContent = "Câmera fechada.";
  } catch (error) {
    console.error("Não foi possível fechar a câmera corretamente.", error);
    showResult("error", "Falha ao fechar a câmera", "Atualize a página se a câmera continuar ativa.");
  } finally {
    startButton.disabled = scannerRunning;
    stopButton.disabled = !scannerRunning;
  }
}

startButton.addEventListener("click", startScanner);
stopButton.addEventListener("click", stopScanner);
window.addEventListener("online", updateNetworkStatus);
window.addEventListener("offline", updateNetworkStatus);
updateNetworkStatus();
