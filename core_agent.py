# core_agent.py
import os
import json
import base64
import re
from openai import OpenAI
from dotenv import load_dotenv
from prompts import SOLVER_SYSTEM_PROMPT, TUTOR_SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

class SocraticMathCoach:
    def __init__(self):
        self.problem_context = ""  
        self.chat_history =[]     

    def analyze_problem(self, math_problem: str = "", image_bytes: bytes = None):
        """
        Agent 1 工作：后台分析数学题（支持图文双输入）
        """
        print("💡 [后台] Agent 1 正在秘密解题（处理多模态数据）...")
        
        content_list =[]
        text_prompt = "请解答这道数学题。"
        if math_problem:
            text_prompt += f"\n补充文字说明/题目内容：{math_problem}"
        content_list.append({"type": "text", "text": text_prompt})

        if image_bytes:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            content_list.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

        try:
            response = client.chat.completions.create(
                model="glm-4v-flash", 
                messages=[
                    {"role": "system", "content": SOLVER_SYSTEM_PROMPT},
                    {"role": "user", "content": content_list}
                ]
            )
            
            raw_content = response.choices[0].message.content
            print(f"[Debug] Agent 1 原始输出: {raw_content}")
            
            match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if match:
                json_str = match.group(0)
                self.problem_context = json_str
                return json.loads(json_str)
            else:
                raise ValueError("未找到有效的 JSON 结构")
            
        except Exception as e:
            print(f"Agent 1 解析失败: {e}")
            self.problem_context = raw_content if 'raw_content' in locals() else "解析出错"
            return {"error": str(e)}

    def chat_with_student(self, student_input: str) -> str:
        """
        Agent 2 工作：根据后台解答，启发式对话
        """
        dynamic_system_prompt = TUTOR_SYSTEM_PROMPT.format(
            background_info=self.problem_context
        )
        
        messages =[{"role": "system", "content": dynamic_system_prompt}]
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": student_input})

        print("🗣️ [前端] Agent 2 正在生成启发式提问...")
        response = client.chat.completions.create(
            model="glm-4-flash", 
            messages=messages,
            temperature=0.6 
        )
        
        tutor_reply = response.choices[0].message.content
        
        self.chat_history.append({"role": "user", "content": student_input})
        self.chat_history.append({"role": "assistant", "content": tutor_reply})
        
        return tutor_reply