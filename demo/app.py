import re
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash,jsonify
import os
import json
from aitestcase3 import WorkflowManager
UPLOAD_FOLDER = '../data'
ALLOWED_EXTENSIONS = {'md'}


app = Flask(__name__)
# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = 'your_secret_key'

# 清理旧的文档
def cleanup_old_file():
    old_file = os.path.join(UPLOAD_FOLDER, 'document.md')
    if os.path.exists(old_file):
        os.remove(old_file)

# 检查文件是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 处理文件上传
@app.route('/', methods=['POST'])
def upload_file():
    # 检查是否有文件部分在请求中
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    # 如果用户没有选择文件，浏览器也会提交一个空的文件名，没有文件内容
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        cleanup_old_file()  # 删除旧的文档
        filename = 'document.md'
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        flash('文件上传成功','success')
        # return f'File {filename} uploaded successfully'
        return redirect(url_for('hello_world'))
    else:
        # return 'File type not allowed'
        flash('文件类型错误，请检查文件类型是否为.md文件', 'error')
        # return f'File {filename} uploaded successfully'
        return redirect(url_for('hello_world'))


@app.route('/run_workflow', methods=['POST'])
def run_workflow():
    manager = WorkflowManager()
    guiding_strategy_path = "../data/编写用例要点.txt"
    case_template_path = "../data/标准用例格式.txt"
    manager.load_strategy_and_template(guiding_strategy_path, case_template_path)
    document_path = "../data/document.md"
    manager.set_requirement_document(document_path)
    test_cases = {}
    test_cases = manager.run_workflow()
    print("结果2:")
    print(test_cases)
    return test_cases



@app.route('/')
def hello_world():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)