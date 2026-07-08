# -*- coding: utf-8 -*-
"""PDF → JPG 변환기 (Windows용 GUI)

PDF 파일을 페이지별 JPG 이미지로 변환합니다.
- 여러 PDF 동시 변환, 드래그 앤 드롭 지원
- 해상도(DPI), JPG 품질, 페이지 범위 지정 가능
"""

import os
import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz  # PyMuPDF

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False


def parse_page_range(text, page_count):
    """'1-3,5,8-10' 형식 문자열을 0-based 페이지 인덱스 리스트로 변환.

    빈 문자열이면 전체 페이지를 반환한다.
    """
    text = text.strip()
    if not text:
        return list(range(page_count))
    pages = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
        elif part.isdigit():
            start = end = int(part)
        else:
            raise ValueError(f"페이지 범위 형식이 잘못되었습니다: '{part}'")
        if start < 1 or end < start:
            raise ValueError(f"페이지 범위가 올바르지 않습니다: '{part}'")
        for p in range(start, end + 1):
            if p <= page_count:
                pages.add(p - 1)
    if not pages:
        raise ValueError("지정한 페이지가 문서 범위를 벗어났습니다.")
    return sorted(pages)


def convert_pdf(pdf_path, out_dir, dpi=200, quality=90, page_range="",
                per_pdf_folder=True, progress=None):
    """PDF 한 개를 JPG들로 변환. 저장된 파일 경로 리스트를 반환."""
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    if per_pdf_folder:
        out_dir = os.path.join(out_dir, stem)
    os.makedirs(out_dir, exist_ok=True)

    saved = []
    with fitz.open(pdf_path) as doc:
        indices = parse_page_range(page_range, doc.page_count)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        digits = max(3, len(str(doc.page_count)))
        for n, i in enumerate(indices, start=1):
            pix = doc[i].get_pixmap(matrix=matrix)
            out_path = os.path.join(out_dir, f"{stem}_{i + 1:0{digits}d}.jpg")
            pix.save(out_path, jpg_quality=quality)
            saved.append(out_path)
            if progress:
                progress(n, len(indices))
    return saved


class App:
    def __init__(self, root):
        self.root = root
        root.title("PDF → JPG 변환기")
        root.geometry("640x560")
        root.minsize(560, 480)

        self.msg_queue = queue.Queue()
        self.converting = False

        pad = {"padx": 10, "pady": 4}

        # ── 파일 목록 ──────────────────────────────────────
        frame_files = ttk.LabelFrame(root, text=" 1. PDF 파일 ")
        frame_files.pack(fill="both", expand=True, **pad)

        self.listbox = tk.Listbox(frame_files, selectmode="extended", height=7)
        self.listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scroll = ttk.Scrollbar(frame_files, command=self.listbox.yview)
        scroll.pack(side="left", fill="y", pady=8)
        self.listbox.config(yscrollcommand=scroll.set)

        btns = ttk.Frame(frame_files)
        btns.pack(side="left", fill="y", padx=8, pady=8)
        ttk.Button(btns, text="PDF 추가...", command=self.add_files).pack(fill="x", pady=2)
        ttk.Button(btns, text="선택 제거", command=self.remove_selected).pack(fill="x", pady=2)
        ttk.Button(btns, text="전체 지우기", command=self.clear_files).pack(fill="x", pady=2)
        hint = "여기로 PDF를\n끌어다 놓아도 돼요" if HAS_DND else ""
        if hint:
            ttk.Label(btns, text=hint, foreground="gray", justify="center").pack(pady=(12, 0))

        if HAS_DND:
            self.listbox.drop_target_register(DND_FILES)
            self.listbox.dnd_bind("<<Drop>>", self.on_drop)

        # ── 저장 위치 ──────────────────────────────────────
        frame_out = ttk.LabelFrame(root, text=" 2. 저장 위치 (비워두면 PDF와 같은 폴더) ")
        frame_out.pack(fill="x", **pad)
        self.out_var = tk.StringVar()
        ttk.Entry(frame_out, textvariable=self.out_var).pack(
            side="left", fill="x", expand=True, padx=8, pady=8)
        ttk.Button(frame_out, text="찾아보기...", command=self.pick_out_dir).pack(
            side="left", padx=(0, 8), pady=8)

        # ── 옵션 ──────────────────────────────────────────
        frame_opt = ttk.LabelFrame(root, text=" 3. 옵션 ")
        frame_opt.pack(fill="x", **pad)

        row = ttk.Frame(frame_opt)
        row.pack(fill="x", padx=8, pady=8)

        ttk.Label(row, text="해상도(DPI):").pack(side="left")
        self.dpi_var = tk.StringVar(value="200")
        ttk.Combobox(row, textvariable=self.dpi_var, width=6, state="readonly",
                     values=["72", "100", "150", "200", "300", "600"]).pack(side="left", padx=(4, 16))

        ttk.Label(row, text="JPG 품질:").pack(side="left")
        self.quality_var = tk.IntVar(value=90)
        ttk.Spinbox(row, from_=10, to=100, increment=5, width=5,
                    textvariable=self.quality_var).pack(side="left", padx=(4, 16))

        ttk.Label(row, text="페이지:").pack(side="left")
        self.pages_var = tk.StringVar()
        entry_pages = ttk.Entry(row, textvariable=self.pages_var, width=12)
        entry_pages.pack(side="left", padx=4)
        ttk.Label(row, text="(예: 1-3,5 / 비우면 전체)", foreground="gray").pack(side="left")

        self.subfolder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_opt, text="PDF마다 하위 폴더를 만들어 저장",
                        variable=self.subfolder_var).pack(anchor="w", padx=8, pady=(0, 8))

        # ── 실행 ──────────────────────────────────────────
        self.btn_convert = ttk.Button(root, text="변환 시작", command=self.start_convert)
        self.btn_convert.pack(fill="x", padx=10, pady=(4, 0), ipady=6)

        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(6, 0))

        self.status_var = tk.StringVar(value="PDF 파일을 추가한 뒤 [변환 시작]을 누르세요.")
        ttk.Label(root, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=10, pady=(4, 10))

        self.root.after(100, self.poll_queue)

    # ── 파일 목록 조작 ─────────────────────────────────────
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="PDF 파일 선택", filetypes=[("PDF 파일", "*.pdf")])
        self.add_paths(paths)

    def add_paths(self, paths):
        existing = set(self.listbox.get(0, "end"))
        for p in paths:
            p = os.path.normpath(p)
            if p.lower().endswith(".pdf") and p not in existing:
                self.listbox.insert("end", p)
                existing.add(p)

    def on_drop(self, event):
        self.add_paths(self.root.tk.splitlist(event.data))

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i)

    def clear_files(self):
        self.listbox.delete(0, "end")

    def pick_out_dir(self):
        d = filedialog.askdirectory(title="저장 폴더 선택")
        if d:
            self.out_var.set(os.path.normpath(d))

    # ── 변환 ─────────────────────────────────────────────
    def start_convert(self):
        if self.converting:
            return
        files = list(self.listbox.get(0, "end"))
        if not files:
            messagebox.showwarning("알림", "변환할 PDF 파일을 먼저 추가하세요.")
            return
        try:
            dpi = int(self.dpi_var.get())
            quality = max(10, min(100, int(self.quality_var.get())))
        except ValueError:
            messagebox.showerror("오류", "해상도/품질 값이 올바르지 않습니다.")
            return

        self.converting = True
        self.btn_convert.config(state="disabled")
        self.progress["value"] = 0

        args = (files, self.out_var.get().strip(), dpi, quality,
                self.pages_var.get(), self.subfolder_var.get())
        threading.Thread(target=self.worker, args=args, daemon=True).start()

    def worker(self, files, out_base, dpi, quality, page_range, per_pdf_folder):
        q = self.msg_queue
        total_saved, errors = 0, []
        last_out_dir = None
        for idx, pdf in enumerate(files, start=1):
            name = os.path.basename(pdf)
            q.put(("status", f"[{idx}/{len(files)}] {name} 변환 중..."))
            out_dir = out_base if out_base else os.path.dirname(pdf)
            try:
                def on_page(done, total, idx=idx, n=len(files)):
                    overall = ((idx - 1) + done / total) / n * 100
                    q.put(("progress", overall))
                saved = convert_pdf(pdf, out_dir, dpi=dpi, quality=quality,
                                    page_range=page_range,
                                    per_pdf_folder=per_pdf_folder, progress=on_page)
                total_saved += len(saved)
                if saved:
                    last_out_dir = os.path.dirname(saved[0])
            except Exception as e:
                errors.append(f"{name}: {e}")
        q.put(("done", (total_saved, errors, last_out_dir)))

    def poll_queue(self):
        try:
            while True:
                kind, data = self.msg_queue.get_nowait()
                if kind == "status":
                    self.status_var.set(data)
                elif kind == "progress":
                    self.progress["value"] = data
                elif kind == "done":
                    self.finish(*data)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def finish(self, total_saved, errors, last_out_dir):
        self.converting = False
        self.btn_convert.config(state="normal")
        self.progress["value"] = 100 if total_saved else 0
        if errors:
            self.status_var.set(f"완료: JPG {total_saved}장 저장, 오류 {len(errors)}건")
            messagebox.showerror("일부 실패", "\n".join(errors))
        elif total_saved:
            self.status_var.set(f"완료! JPG {total_saved}장이 저장되었습니다.")
            if last_out_dir and messagebox.askyesno(
                    "변환 완료", f"JPG {total_saved}장을 저장했습니다.\n저장 폴더를 열까요?"):
                os.startfile(last_out_dir)
        else:
            self.status_var.set("저장된 파일이 없습니다.")


def main():
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
