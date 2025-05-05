import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
import threading
import base64
import io
from PIL import Image, ImageTk
import os
import json
import re # 导入 re 模块

# --- API 配置 ---
IMAGE_API_URL = "https://api.siliconflow.cn/v1/images/generations"
# 更新模型列表为您指定的模型
MODELS = [
    "Kwai-Kolors/Kolors",
    "black-forest-labs/FLUX.1-schnell",
    "black-forest-labs/FLUX.1-dev",
    "Pro/black-forest-labs/FLUX.1-schnell", # 注意：API 可能需要不同的标识符
    "stabilityai/stable-diffusion-3-5-large", # 注意：API 可能需要不同的标识符
    "black-forest-labs/FLUX.1-pro", # 注意：API 可能需要不同的标识符
    "LoRA/black-forest-labs/FLUX.1-dev", # 注意：API 可能需要不同的标识符
    "stabilityai/stable-diffusion-xl-base-1.0",
]
# 设置默认模型
DEFAULT_MODEL = "Kwai-Kolors/Kolors"
IMAGE_SIZES = [
    "1024x1024", "512x512", "1024x768", "768x1024", "1024x576", "576x1024",
]
DEFAULT_SIZE = "1024x1024"
DEFAULT_API_KEY = "sk-leirgmdwwghisduaqjb" # 添加默认 API Key

# --- 主应用类 ---
class SiliconFlowImageGenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SiliconFlow 文生图 GUI")
        self.geometry("800x750")

        # 设置默认 API Key
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.size_var = tk.StringVar(value=DEFAULT_SIZE)
        self.steps_var = tk.IntVar(value=25)
        self.cfg_scale_var = tk.DoubleVar(value=7.0)
        self.seed_var = tk.StringVar(value="")
        self.image_data_bytes = None
        self.photo_image = None

        self._create_widgets()

    def _create_widgets(self):
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        control_frame = ttk.Frame(paned_window, width=350, height=700)
        control_frame.pack_propagate(False)
        paned_window.add(control_frame, weight=1)

        api_frame = ttk.LabelFrame(control_frame, text="API Key", padding="5")
        api_frame.pack(fill=tk.X, pady=5, padx=5)
        # API Key 输入框现在会显示默认值
        ttk.Entry(api_frame, textvariable=self.api_key, width=40, show="*").pack(fill=tk.X, expand=True)

        prompt_frame = ttk.LabelFrame(control_frame, text="Prompt (描述图像)", padding="5")
        prompt_frame.pack(fill=tk.X, pady=5, padx=5)
        self.prompt_input = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=6, width=40)
        self.prompt_input.pack(fill=tk.X, expand=True)

        neg_prompt_frame = ttk.LabelFrame(control_frame, text="Negative Prompt (不希望出现)", padding="5")
        neg_prompt_frame.pack(fill=tk.X, pady=5, padx=5)
        self.neg_prompt_input = scrolledtext.ScrolledText(neg_prompt_frame, wrap=tk.WORD, height=4, width=40)
        self.neg_prompt_input.pack(fill=tk.X, expand=True)

        params_frame = ttk.LabelFrame(control_frame, text="参数设置", padding="5")
        params_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(params_frame, text="模型:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        # 使用更新后的模型列表
        model_menu = ttk.Combobox(params_frame, textvariable=self.model_var, values=MODELS, state="readonly", width=35) # 增加宽度以显示完整名称
        model_menu.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

        ttk.Label(params_frame, text="尺寸:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        size_menu = ttk.Combobox(params_frame, textvariable=self.size_var, values=IMAGE_SIZES, state="readonly", width=15)
        size_menu.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

        ttk.Label(params_frame, text="步数 (Steps):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        steps_spinbox = ttk.Spinbox(params_frame, from_=1, to=100, textvariable=self.steps_var, width=8)
        steps_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(params_frame, text="引导系数 (CFG):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        cfg_scale = ttk.Scale(params_frame, from_=0.0, to=20.0, variable=self.cfg_scale_var, orient=tk.HORIZONTAL, length=100)
        cfg_scale.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        cfg_label = ttk.Label(params_frame, textvariable=self.cfg_scale_var)
        cfg_label.grid(row=3, column=2, padx=2, pady=5, sticky=tk.W)

        ttk.Label(params_frame, text="种子 (Seed):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        seed_entry = ttk.Entry(params_frame, textvariable=self.seed_var, width=15)
        seed_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(params_frame, text="(留空则随机)").grid(row=5, column=1, columnspan=2, padx=5, pady=2, sticky=tk.W)

        action_frame = ttk.Frame(control_frame, padding="10")
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        self.generate_button = ttk.Button(action_frame, text="生成图像", command=self._start_generate_thread, width=12)
        self.generate_button.pack(side=tk.LEFT, padx=10)

        self.save_button = ttk.Button(action_frame, text="保存图像", command=self._save_image, state=tk.DISABLED, width=12)
        self.save_button.pack(side=tk.RIGHT, padx=10)

        image_frame = ttk.Frame(paned_window, width=400, height=700)
        paned_window.add(image_frame, weight=2)

        self.image_label = ttk.Label(image_frame, text="生成的图像将显示在这里", anchor=tk.CENTER, relief=tk.GROOVE)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.status_label = ttk.Label(self, text="状态：准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def _set_status(self, message):
        self.status_label.config(text=f"状态：{message}")
        self.update_idletasks()

    def _toggle_buttons(self, enable_generate, enable_save):
        self.generate_button.config(state=tk.NORMAL if enable_generate else tk.DISABLED)
        self.save_button.config(state=tk.NORMAL if enable_save else tk.DISABLED)

    def _start_generate_thread(self):
        api_key = self.api_key.get()
        prompt = self.prompt_input.get("1.0", tk.END).strip()

        if not api_key:
            messagebox.showerror("错误", "请输入 API Key。")
            return
        if not prompt:
            messagebox.showerror("错误", "请输入 Prompt。")
            return

        self._set_status("正在生成图像...")
        self._toggle_buttons(False, False)
        self.image_data_bytes = None
        self.image_label.config(image='', text="正在生成...")
        self.update_idletasks()

        thread = threading.Thread(target=self._generate_image, args=(api_key, prompt), daemon=True)
        thread.start()

    def _generate_image(self, api_key, prompt):
        neg_prompt = self.neg_prompt_input.get("1.0", tk.END).strip()
        model = self.model_var.get()
        size_str = self.size_var.get()
        steps = self.steps_var.get()
        cfg = self.cfg_scale_var.get()
        seed_str = self.seed_var.get()

        try:
            width, height = map(int, size_str.split('x'))
        except ValueError:
            messagebox.showerror("错误", "无效的图像尺寸格式。")
            self.after(0, self._set_status, "生成失败：无效尺寸")
            self.after(0, self._toggle_buttons, True, False)
            return

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "guidance_scale": cfg,
        }
        if neg_prompt:
            payload["negative_prompt"] = neg_prompt
        if seed_str.isdigit():
            payload["seed"] = int(seed_str)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(IMAGE_API_URL, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            print("--- DEBUG: Full API Response ---")
            print(result)
            print("--- END DEBUG ---")

            # 完全不同的方法：直接搜索响应文本中的URL
            response_text = json.dumps(result)

            # 查找所有包含 "url" 的键值对
            image_url = None

            # 尝试从 images 字段获取
            if 'images' in result and isinstance(result['images'], list) and len(result['images']) > 0:
                if isinstance(result['images'][0], dict) and 'url' in result['images'][0]: # 修正：检查 images[0]
                    image_url = result['images'][0]['url']
                    print(f"--- DEBUG: Found URL in images[0]['url']: {image_url}")

            # 如果上面失败，尝试从 data 字段获取
            if not image_url and 'data' in result and isinstance(result['data'], list) and len(result['data']) > 0:
                 if isinstance(result['data'][0], dict) and 'url' in result['data'][0]: # 修正：检查 data[0]
                    image_url = result['data'][0]['url']
                    print(f"--- DEBUG: Found URL in data[0]['url']: {image_url}")

            # 如果还是没找到，尝试直接从响应文本中提取URL
            if not image_url:
                url_matches = re.findall(r'https://[^"\']+\.(?:png|jpg|jpeg|gif)', response_text)
                if url_matches:
                    # **最终修正：只取第一个匹配的 URL**
                    image_url = url_matches[0] # <--- THE ACTUAL, FINAL, CORRECT FIX!
                    print(f"--- DEBUG: Extracted URL using regex: {image_url}")

            if image_url:
                # 现在 image_url 必然是字符串（如果找到了的话）
                self._set_status(f"获取到图像 URL: {image_url[:50]}...")
                try:
                    print(f"--- DEBUG: Attempting to download image from URL...")
                    print(f"--- DEBUG: URL to download: {image_url}") # 打印最终用于下载的URL

                    image_response = requests.get(image_url, timeout=60) # 直接使用 image_url 字符串
                    image_response.raise_for_status()
                    self.image_data_bytes = image_response.content
                    print(f"--- DEBUG: Image downloaded successfully ({len(self.image_data_bytes)} bytes).")
                    self._set_status("图像下载成功！")
                    self.after(0, self._display_image)
                    self.after(0, self._toggle_buttons, True, True)
                except requests.exceptions.RequestException as img_e:
                    error_msg = f"从 URL 下载图像失败: {img_e}"
                    print(f"--- DEBUG: Image download failed ---")
                    print(f"URL used for download: {image_url}") # 打印用于下载的 URL
                    print(f"Error: {img_e}")
                    print(f"--- END DEBUG ---")
                    messagebox.showerror("下载错误", f"{error_msg}\n\n请检查控制台输出。")
                    self.after(0, self._set_status, "图像下载失败")
                    self.after(0, self._toggle_buttons, True, False)
                except Exception as display_e:
                    messagebox.showerror("处理错误", f"下载或处理图像时出错: {display_e}")
                    self.after(0, self._set_status, "图像处理失败")
                    self.after(0, self._toggle_buttons, True, False)
            else:
                error_msg = "无法从 API 响应中提取图像 URL"
                messagebox.showerror("API 错误", f"生成失败: {error_msg}\n\n请检查控制台输出获取详细的 API 响应内容。")
                self.after(0, self._set_status, f"生成失败: {error_msg}")
                self.after(0, self._toggle_buttons, True, False)

        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_message += f"\n错误详情: {error_detail.get('error', {}).get('message', e.response.text)}"
                except ValueError:
                    error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message)
            self.after(0, self._set_status, "生成失败")
            self.after(0, self._toggle_buttons, True, False)
        except Exception as e:
            messagebox.showerror("错误", f"发生意外错误: {e}")
            self.after(0, self._set_status, "生成失败")
            self.after(0, self._toggle_buttons, True, False)

    def _display_image(self):
        if not self.image_data_bytes:
            return

        try:
            img = Image.open(io.BytesIO(self.image_data_bytes))
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()
            if label_width < 10 or label_height < 10:
                label_width, label_height = 400, 400
            img.thumbnail((label_width - 20, label_height - 20), Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo_image, text="")
        except Exception as e:
            messagebox.showerror("显示错误", f"无法显示图像: {e}")
            self.image_label.config(image='', text="无法显示图像")
            self._set_status("图像显示失败")

    def _save_image(self):
        if not self.image_data_bytes:
            messagebox.showwarning("警告", "没有可保存的图像数据。请先生成图像。")
            return

        try:
            img_format = Image.open(io.BytesIO(self.image_data_bytes)).format
            if not img_format: img_format = 'png'
        except Exception:
            img_format = 'png'

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{img_format.lower()}",
            filetypes=[(f"{img_format.upper()} 文件", f"*.{img_format.lower()}"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, "wb") as f:
                    f.write(self.image_data_bytes)
                self._set_status(f"图像已保存到: {file_path}")
                messagebox.showinfo("成功", f"图像文件已成功保存到\n{file_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"无法保存文件: {e}")
                self._set_status("保存失败")
        else:
            self._set_status("保存操作已取消")

# --- 启动应用 ---
if __name__ == "__main__":
    app = SiliconFlowImageGenApp()
    app.mainloop()