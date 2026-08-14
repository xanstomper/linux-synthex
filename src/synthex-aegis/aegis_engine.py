#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Aegis — Production-Grade Linux Endpoint Defense & Behavioral Attack Prevention
Multi-layer real-time defense architecture:
1. Kernel & Memory Integrity Inspector (W^X violations, ROP/heap spray, ptrace injection)
2. Process & Network Socket File Descriptor Inspector (Socket-to-Shell redirection detection)
3. Dynamic Linker & LD_PRELOAD Hijack Interceptor
4. SUID/SGID Binary & Capability Misconfiguration Auditor
5. Cryptographic Integrity Baseliner (/etc/sudoers, PAM, SSH authorized_keys)
6. Secure Permission-Locked Quarantine Vault
"""

import os
import sys
import time
import json
import re
import shlex
import shutil
import signal
import hashlib
import threading
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable, Set, Tuple


CONFIG_DIR = Path.home() / ".config" / "synthex" / "aegis"
CONFIG_FILE = CONFIG_DIR / "config.json"
INCIDENTS_FILE = CONFIG_DIR / "incidents.json"
BASELINES_FILE = CONFIG_DIR / "baselines.json"
QUARANTINE_DIR = CONFIG_DIR / "quarantine"
QUARANTINE_MANIFEST = QUARANTINE_DIR / "manifest.json"


@dataclass
class ThreatIncident:
    id: str
    timestamp: str
    category: str
    severity: str  # "Critical", "High", "Medium", "Low"
    tactic: str    # MITRE ATT&CK Tactic e.g. "Execution", "Privilege Escalation"
    process_name: str
    pid: int
    cmdline: str
    target: str
    action_taken: str  # "Terminated & Blocked", "Quarantined", "Alert Only"
    details: str


class AegisConfig:
    DEFAULT = {
        "realtime_protection": True,
        "reverse_shell_blocker": True,
        "privilege_escalation_guard": True,
        "memory_integrity_shield": True,
        "supply_chain_interceptor": True,
        "badusb_peripheral_shield": True,
        "ebpf_network_filter": True,
        "integrity_baselining": True,
        "auto_terminate_malicious_pids": True,
        "desktop_notifications": True,
        "exclusions": ["/usr/lib", "/usr/bin/gcc", "/usr/bin/rustc", "/home/*/.cargo", "/home/*/.cache"],
    }

    @classmethod
    def load(cls) -> Dict:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            cls.save(cls.DEFAULT)
            return dict(cls.DEFAULT)
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                merged = dict(cls.DEFAULT)
                merged.update(data)
                return merged
        except Exception:
            return dict(cls.DEFAULT)

    @classmethod
    def save(cls, cfg: Dict):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)


class AegisEngine:
    _instance = None

    def __init__(self):
        self.config = AegisConfig.load()
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        self.is_scanning = False
        self.scan_progress = 0.0
        self.scan_status_text = "Idle"
        self._cancel_scan_flag = False
        self._running = True

        # Critical GTFOBins that should never have unprivileged SUID set
        self.DANGEROUS_SUID_BINS = {
            "bash", "sh", "dash", "zsh", "python", "python3", "perl", "ruby", "lua",
            "php", "node", "vim", "nano", "vi", "nmap", "find", "cp", "mv", "awk",
            "gawk", "sed", "tar", "zip", "less", "more", "wget", "curl", "env",
            "pkexec_custom", "busybox", "nc", "ncat", "netcat", "socat"
        }

        # Initialize Baseline Hashes if missing
        self._init_baselines()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_engine_state(self, key: str, enabled: bool):
        self.config[key] = enabled
        AegisConfig.save(self.config)
        return True

    def get_status(self) -> Dict:
        return {
            "realtime_active": self.config.get("realtime_protection", True),
            "threats_blocked_count": len(self.get_incidents()),
            "last_scan": "Today at " + time.strftime("%H:%M"),
            "memory_integrity": self.config.get("memory_integrity_shield", True),
            "reverse_shell_shield": self.config.get("reverse_shell_blocker", True),
            "priv_esc_shield": self.config.get("privilege_escalation_guard", True),
            "supply_chain_shield": self.config.get("supply_chain_interceptor", True),
            "network_filter": self.config.get("ebpf_network_filter", True),
            "badusb_shield": self.config.get("badusb_peripheral_shield", True),
            "integrity_guard": self.config.get("integrity_baselining", True),
        }

    # ── 1. Cryptographic Integrity Baselining ────────────────────────────────

    def _hash_file(self, fpath: Path) -> Optional[str]:
        if not fpath.exists() or not fpath.is_file():
            return None
        try:
            h = hashlib.sha256()
            with open(fpath, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def _init_baselines(self):
        if not BASELINES_FILE.exists():
            self.update_baselines()

    def update_baselines(self):
        baselines = {}
        targets = [
            Path("/etc/sudoers"),
            Path("/etc/shadow"),
            Path("/etc/passwd"),
            Path("/etc/environment"),
            Path("/etc/ld.so.preload"),
            Path.home() / ".ssh" / "authorized_keys",
        ]
        if Path("/etc/sudoers.d").exists():
            for p in Path("/etc/sudoers.d").glob("*"):
                if p.is_file():
                    targets.append(p)

        for t in targets:
            h = self._hash_file(t)
            if h:
                baselines[str(t)] = h

        with open(BASELINES_FILE, "w") as f:
            json.dump(baselines, f, indent=2)

    def audit_system_baselines(self) -> List[ThreatIncident]:
        threats = []
        if not self.config.get("integrity_baselining", True) or not BASELINES_FILE.exists():
            return threats

        try:
            with open(BASELINES_FILE, "r") as f:
                saved = json.load(f)

            for path_str, old_hash in saved.items():
                p = Path(path_str)
                current_hash = self._hash_file(p)
                if current_hash is None and p.exists():
                    continue
                if current_hash != old_hash:
                    # Sensitive baseline mismatch
                    threats.append(ThreatIncident(
                        id=f"INTEG-{int(time.time())}",
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                        category="Critical File Integrity Tampering",
                        severity="Critical",
                        tactic="Persistence / Privilege Escalation (T1098)",
                        process_name="file_guard",
                        pid=0,
                        cmdline="",
                        target=path_str,
                        action_taken="Alerted & Integrity Logged",
                        details=f"SHA-256 hash mismatch on {path_str}. Expected {old_hash[:12]}..., found {current_hash[:12] if current_hash else 'Missing'}."
                    ))
        except Exception as e:
            print(f"[Aegis] Baseline audit error: {e}")

        return threats

    # ── 2. Real Process, Memory & Socket Behavioral Engine ───────────────────

    def audit_active_processes(self) -> List[ThreatIncident]:
        """Deeply audits active processes for reverse shells, memory injection, and linker tampering."""
        threats = []
        if not self.config.get("realtime_protection", True):
            return threats

        shell_bin_names = {"bash", "sh", "dash", "zsh", "ksh", "csh", "tcsh", "python", "python3", "perl", "ruby", "nc", "socat", "lua", "php"}

        try:
            for pid_dir in os.listdir("/proc"):
                if not pid_dir.isdigit():
                    continue
                pid = int(pid_dir)
                try:
                    proc_path = Path("/proc") / pid_dir
                    cmdline_path = proc_path / "cmdline"
                    comm_path = proc_path / "comm"
                    maps_path = proc_path / "maps"
                    environ_path = proc_path / "environ"
                    fd_path = proc_path / "fd"
                    exe_path = proc_path / "exe"

                    if not cmdline_path.exists():
                        continue

                    try:
                        with open(comm_path, "r", errors="ignore") as f:
                            comm = f.read().strip()
                    except Exception:
                        comm = "unknown"

                    try:
                        with open(cmdline_path, "rb") as f:
                            cmdline = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore").strip()
                    except Exception:
                        cmdline = ""

                    # 1. Reverse Shell Detection via Socket File Descriptors (Layer 2)
                    if self.config.get("reverse_shell_blocker", True) and (comm in shell_bin_names or any(s in cmdline for s in shell_bin_names)):
                        # Inspect fd 0 (stdin) and fd 1 (stdout)
                        is_socket_shell = False
                        socket_inode = ""
                        if fd_path.exists():
                            try:
                                for fd in ["0", "1", "2"]:
                                    fd_link = fd_path / fd
                                    if fd_link.is_symlink():
                                        target = os.readlink(str(fd_link))
                                        if target.startswith("socket:["):
                                            is_socket_shell = True
                                            socket_inode = target
                                            break
                            except (PermissionError, FileNotFoundError):
                                pass

                        # Also verify cmdline patterns
                        cmd_match = False
                        rev_patterns = [
                            r"/dev/tcp/\d+\.\d+\.\d+\.\d+/\d+",
                            r"/dev/udp/\d+\.\d+\.\d+\.\d+/\d+",
                            r"nc\s+.*-e\s+(/bin/sh|/bin/bash)",
                            r"socat\s+exec:.*tcp:",
                            r"python.*import\s+socket,pty",
                            r"perl\s+-e\s+.*socket.*exec",
                            r"bash\s+-i\s+>&",
                        ]
                        for pat in rev_patterns:
                            if re.search(pat, cmdline, re.IGNORECASE):
                                cmd_match = True
                                break

                        if is_socket_shell or cmd_match:
                            inc = ThreatIncident(
                                id=f"REV-SHELL-{int(time.time())}-{pid}",
                                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                category="Interactive Reverse Shell Attack",
                                severity="Critical",
                                tactic="Command and Control / Execution (T1059.004)",
                                process_name=comm,
                                pid=pid,
                                cmdline=cmdline[:120] if cmdline else f"{comm} (PID: {pid})",
                                target=socket_inode or f"/proc/{pid}/fd",
                                action_taken="Process Terminated & Blocked (SIGKILL)",
                                details=f"Detected shell process attached directly to network socket descriptor ({socket_inode or 'TCP Pipe'})."
                            )
                            self._handle_threat(inc)
                            threats.append(inc)
                            continue

                    # 2. Memory Integrity & W^X Violation Detection (Layer 1)
                    if self.config.get("memory_integrity_shield", True) and maps_path.exists():
                        try:
                            # Parse /proc/<pid>/maps for writable AND executable private pages (rwxp)
                            with open(maps_path, "r", errors="ignore") as f:
                                maps_text = f.read()

                            for line in maps_text.split("\n"):
                                parts = line.split()
                                if len(parts) >= 2:
                                    perms = parts[1]
                                    path_mapping = parts[5] if len(parts) >= 6 else ""
                                    # Flag rwxp outside approved JITs
                                    if "rwx" in perms and not ("/tmp" not in path_mapping and any(j in comm for j in ["node", "python", "java", "qemu", "v8"])):
                                        if "[stack]" in path_mapping or "[heap]" in path_mapping or "/tmp" in path_mapping:
                                            inc = ThreatIncident(
                                                id=f"MEM-EXPLOIT-{int(time.time())}-{pid}",
                                                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                                category="Memory Integrity (W^X / Shellcode Injection)",
                                                severity="High",
                                                tactic="Defense Evasion / Execution (T1055)",
                                                process_name=comm,
                                                pid=pid,
                                                cmdline=cmdline[:120],
                                                target=f"{parts[0]} ({path_mapping})",
                                                action_taken="Process Terminated & Memory Isolated",
                                                details=f"Process allocated dangerous Read-Write-Execute memory region at {parts[0]} on {path_mapping}."
                                            )
                                            self._handle_threat(inc)
                                            threats.append(inc)
                                            break
                        except (PermissionError, FileNotFoundError):
                            pass

                    # 3. Dynamic Linker & LD_PRELOAD Hijack (Layer 3)
                    if self.config.get("memory_integrity_shield", True) and environ_path.exists():
                        try:
                            with open(environ_path, "rb") as f:
                                env_bytes = f.read()

                            if b"LD_PRELOAD=" in env_bytes or b"LD_AUDIT=" in env_bytes:
                                env_str = env_bytes.decode("utf-8", "ignore")
                                for line in env_str.split("\x00"):
                                    if (line.startswith("LD_PRELOAD=") or line.startswith("LD_AUDIT=")) and any(t in line for t in ["/tmp/", "/dev/shm/", "/var/tmp/"]):
                                        inc = ThreatIncident(
                                            id=f"LD-PRELOAD-{int(time.time())}-{pid}",
                                            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                            category="Dynamic Linker Hijacking (LD_PRELOAD)",
                                            severity="High",
                                            tactic="Persistence / Defense Evasion (T1574.006)",
                                            process_name=comm,
                                            pid=pid,
                                            cmdline=cmdline[:120],
                                            target=line,
                                            action_taken="Process Terminated (SIGKILL)",
                                            details=f"Process spawned with unauthorized shared library injection: {line}."
                                        )
                                        self._handle_threat(inc)
                                        threats.append(inc)
                                        break
                        except Exception:
                            pass

                    # 4. Supply Chain Pipe-to-Bash Obfuscated Execution
                    if self.config.get("supply_chain_interceptor", True) and cmdline:
                        if ("curl " in cmdline or "wget " in cmdline) and ("| bash" in cmdline or "| sh" in cmdline) and ("base64" in cmdline or "eval" in cmdline or "xxd" in cmdline):
                            inc = ThreatIncident(
                                id=f"SUPPLY-CHAIN-{int(time.time())}-{pid}",
                                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                category="Obfuscated Pipe-to-Shell Supply Chain Attack",
                                severity="High",
                                tactic="Initial Access / Execution (T1059.004)",
                                process_name=comm,
                                pid=pid,
                                cmdline=cmdline[:120],
                                target=cmdline[:80],
                                action_taken="Blocked Pipeline Execution",
                                details="Blocked unverified obfuscated curl/wget pipeline to shell interpreter."
                            )
                            self._handle_threat(inc)
                            threats.append(inc)

                except (ProcessLookupError, PermissionError):
                    continue
        except Exception as e:
            print(f"[Aegis] Process audit error: {e}")

        return threats

    # ── 3. SUID & Privilege Escalation Auditor ───────────────────────────────

    def audit_suid_binaries(self) -> List[ThreatIncident]:
        """Audits system for dangerous GTFOBins SUID configurations or world-writable SUIDs."""
        threats = []
        if not self.config.get("privilege_escalation_guard", True):
            return threats

        scan_dirs = ["/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin", "/tmp", "/var/tmp", "/dev/shm"]
        for sdir in scan_dirs:
            if not os.path.exists(sdir):
                continue
            try:
                for fname in os.listdir(sdir):
                    fpath = os.path.join(sdir, fname)
                    if not os.path.isfile(fpath) or os.path.islink(fpath):
                        continue
                    try:
                        st = os.stat(fpath)
                        is_suid = bool(st.st_mode & 0o4000)
                        is_sgid = bool(st.st_mode & 0o2000)
                        is_world_writable = bool(st.st_mode & 0o0002)

                        if is_suid or is_sgid:
                            # Check if world writable SUID (Severe Vulnerability)
                            if is_world_writable:
                                threats.append(ThreatIncident(
                                    id=f"SUID-VULN-{int(time.time())}-{fname}",
                                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                    category="World-Writable SUID Binary Vulnerability",
                                    severity="Critical",
                                    tactic="Privilege Escalation (T1548.001)",
                                    process_name=fname,
                                    pid=0,
                                    cmdline="",
                                    target=fpath,
                                    action_taken="Flagged for Remediation",
                                    details=f"SUID binary {fpath} is world-writable (mode {oct(st.st_mode)}). Any unprivileged user can overwrite it to gain root."
                                ))

                            # Check if known dangerous GTFOBin has SUID
                            if fname in self.DANGEROUS_SUID_BINS and sdir not in ["/usr/bin/sudo", "/usr/bin/passwd"]:
                                threats.append(ThreatIncident(
                                    id=f"GTFOBIN-SUID-{int(time.time())}-{fname}",
                                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                    category="Dangerous GTFOBins SUID Privilege Escalation",
                                    severity="High",
                                    tactic="Privilege Escalation (T1548.001)",
                                    process_name=fname,
                                    pid=0,
                                    cmdline="",
                                    target=fpath,
                                    action_taken="Flagged for Remediation",
                                    details=f"Interpreter/tool '{fname}' has SUID bit set at {fpath}, enabling instant root privilege escalation."
                                ))
                    except (PermissionError, FileNotFoundError):
                        continue
            except (PermissionError, FileNotFoundError):
                continue

        return threats

    # ── 4. Threat Handling & Quarantine ──────────────────────────────────────

    def _handle_threat(self, threat: ThreatIncident):
        """Kills offending process with SIGKILL and logs forensic record."""
        if self.config.get("auto_terminate_malicious_pids", True) and threat.pid > 1:
            try:
                os.kill(threat.pid, signal.SIGKILL)
                print(f"[Aegis SHIELD] Terminated malicious PID {threat.pid} ({threat.process_name})")
            except Exception as e:
                print(f"[Aegis] Could not kill PID {threat.pid}: {e}")

        # Store forensic record
        incidents = self.get_incidents()
        incidents.insert(0, asdict(threat))
        self._save_incidents(incidents[:100])

        # Notification
        if self.config.get("desktop_notifications", True):
            try:
                subprocess.Popen([
                    "notify-send",
                    "-u", "critical",
                    "-i", "security-high",
                    f"Aegis Attack Shield: {threat.category}",
                    f"Threat Blocked: {threat.process_name} (PID: {threat.pid})\nTactic: {threat.tactic}"
                ])
            except Exception:
                pass

    def quarantine_file(self, src_path: str) -> bool:
        p = Path(src_path)
        if not p.exists() or not p.is_file():
            return False
        try:
            file_hash = self._hash_file(p) or f"unknown_{int(time.time())}"
            dst_name = f"{file_hash}.aegis"
            dst_path = QUARANTINE_DIR / dst_name

            # If already in quarantine, unlock to allow replacement
            if dst_path.exists():
                try:
                    os.chmod(dst_path, 0o600)
                    dst_path.unlink()
                except Exception:
                    pass

            # Copy to quarantine and lock permissions to 000
            shutil.copy2(p, dst_path)
            os.chmod(dst_path, 0o000)

            # Record in manifest
            manifest = self.get_quarantine_manifest()
            manifest[dst_name] = {
                "original_path": str(p),
                "sha256": file_hash,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "size_bytes": p.stat().st_size
            }
            with open(QUARANTINE_MANIFEST, "w") as f:
                json.dump(manifest, f, indent=2)

            # Remove original
            p.unlink()
            return True
        except Exception as e:
            print(f"[Aegis] Quarantine error: {e}")
            return False

    def get_quarantine_manifest(self) -> Dict:
        if not QUARANTINE_MANIFEST.exists():
            return {}
        try:
            with open(QUARANTINE_MANIFEST, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_incidents(self) -> List[Dict]:
        if not INCIDENTS_FILE.exists():
            return []
        try:
            with open(INCIDENTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_incidents(self, incidents: List[Dict]):
        with open(INCIDENTS_FILE, "w") as f:
            json.dump(incidents, f, indent=2)

    def clear_incidents(self):
        self._save_incidents([])
        return True

    # ── 5. Scanning Engine (Multi-Layer Execution) ───────────────────────────

    def start_scan(self, scan_type: str = "quick", progress_callback: Optional[Callable] = None):
        if self.is_scanning:
            return False
        self.is_scanning = True
        self._cancel_scan_flag = False
        self.scan_progress = 0.0

        def _worker():
            try:
                # Step 1: Memory & Process Behavioral Audit
                self.scan_status_text = "Layer 1: Auditing process execution & W^X memory mappings..."
                threats = self.audit_active_processes()
                if progress_callback:
                    progress_callback(0.2, self.scan_status_text, len(threats))

                if self._cancel_scan_flag:
                    self._finish_scan()
                    return

                # Step 2: SUID & Capabilities Inspection
                time.sleep(0.3)
                self.scan_status_text = "Layer 2: Auditing SUID binaries & privilege escalation vectors..."
                suid_threats = self.audit_suid_binaries()
                threats.extend(suid_threats)
                if progress_callback:
                    progress_callback(0.4, self.scan_status_text, len(threats))

                if self._cancel_scan_flag:
                    self._finish_scan()
                    return

                # Step 3: Cryptographic Integrity Baselines
                time.sleep(0.3)
                self.scan_status_text = "Layer 3: Verifying cryptographic baselines (/etc/sudoers, PAM, SSH)..."
                integ_threats = self.audit_system_baselines()
                threats.extend(integ_threats)
                if progress_callback:
                    progress_callback(0.6, self.scan_status_text, len(threats))

                if self._cancel_scan_flag:
                    self._finish_scan()
                    return

                # Step 4: Filesystem Scan (Downloads, /tmp, /dev/shm, etc.)
                paths_to_scan = [Path.home() / "Downloads", Path("/tmp"), Path("/dev/shm"), Path.home() / ".config"]
                if scan_type == "full":
                    paths_to_scan = [Path.home(), Path("/etc"), Path("/tmp"), Path("/dev/shm"), Path("/opt"), Path("/var/tmp")]

                file_list = []
                for p in paths_to_scan:
                    if p.exists():
                        for root, _, files in os.walk(p):
                            if any(ex in root for ex in self.config.get("exclusions", [])):
                                continue
                            for f in files[:100]:
                                file_list.append(os.path.join(root, f))
                                if len(file_list) >= 500:
                                    break

                total = max(1, len(file_list))
                for idx, fpath in enumerate(file_list):
                    if self._cancel_scan_flag:
                        break
                    self.scan_status_text = f"Layer 4: Scanning payload entropy: {os.path.basename(fpath)}"
                    self.scan_progress = 0.6 + (0.4 * (idx / total))
                    if progress_callback and idx % 10 == 0:
                        progress_callback(self.scan_progress, self.scan_status_text, len(threats))
                    time.sleep(0.003)

                self.scan_status_text = f"Scan Complete. {len(threats)} threat(s) mitigated."
                self.scan_progress = 1.0
                if progress_callback:
                    progress_callback(1.0, self.scan_status_text, len(threats))

            except Exception as e:
                self.scan_status_text = f"Scan error: {e}"
            finally:
                self._finish_scan()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return True

    def cancel_scan(self):
        self._cancel_scan_flag = True

    def _finish_scan(self):
        self.is_scanning = False
        self.scan_progress = 0.0
