from openai import OpenAI
import json

API_KEY = "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" # <--- Dán API Key của bạn vào đây

client = OpenAI(api_key=API_KEY)

def grade_submission(assignment_content: str, student_answer: str, max_score: float):
    
    prompt = f"""
    Bạn là một giáo viên công tâm. Hãy chấm điểm bài làm của học sinh dựa trên thông tin sau:
    
    - Đề bài: "{assignment_content}"
    - Thang điểm tối đa: {max_score}
    - Câu trả lời của học sinh: "{student_answer}"

    Yêu cầu output: Hãy trả về kết quả dưới dạng JSON (chỉ JSON, không có markdown) với 2 trường:
    1. "score": Số điểm học sinh đạt được (kiểu số thực, không được vượt quá {max_score}).
    2. "feedback": Lời nhận xét chi tiết, giải thích lỗi sai và khen ngợi (bằng tiếng Việt).
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "Bạn là trợ lý chấm thi tự động."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
        )

        content = response.choices[0].message.content
        
        content = content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(content)
        return result.get("score", 0), result.get("feedback", "Không có nhận xét.")

    except Exception as e:
        print(f"Lỗi AI: {e}")
        return 0, f"Lỗi hệ thống chấm điểm tự động: {str(e)}"