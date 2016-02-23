from flask import Flask, render_template, redirect, url_for, abort, g
from threading import Thread
import os
import random
import string
import time
import json

app = Flask(__name__)
root_path = "/data"

def get_tasks():
    tasks = {}
    try:
        with open("tasks.json", "r") as f:
            tasks = json.load(f)
    except Exception as e:
        pass
    return tasks

def edit_tasks(handler):
    tasks = get_tasks()
    with open("tasks.json", "w") as f:
        tasks = handler(tasks)
        json.dump(tasks, f)

def clean_path(path, directory=False):
    path = os.path.normpath("/" + path)
    if directory and path[-1] != "/":
        path += "/"
    return path

def ls(path):
    path = clean_path(path, True)
    fullpath = root_path + path
    files = []
    id_ = 0
    try:
        for name in os.listdir(fullpath):
            if os.path.isdir(os.path.join(fullpath, name)):
                files.append({"type": "directory", "name": name, "id": id_})
            elif os.path.isfile(os.path.join(fullpath, name)):
                files.append({"type": "file", "name": name, "id": id_})
            id_ += 1
    except:
        return render_template('message.html', message="File not found")
    return render_template('main.html', **locals())

@app.route('/')
def route_home():
    return ls("")

@app.route('/<path:path>')
def route_main(path):
    return ls(path)

def exec_task(task_id):
    tasks_ = {}
    status = None
    result = None

    def status_running(tasks):
        tasks_[task_id] = dict(tasks[task_id])
        tasks[task_id]["status"] = "running"
        return tasks

    def finish_task(tasks):
        tasks[task_id]["status"] = status
        tasks[task_id]["result"] = result
        return tasks

    edit_tasks(status_running)
    try:
        task = tasks_[task_id]
        import zipfile
        zip_name = task["path"][:-1] + "-" + task_id + ".zip"
        len_prefix = len(os.path.dirname(root_path + task["path"][:-1]))
        zf = zipfile.ZipFile(root_path + zip_name, "w", zipfile.ZIP_DEFLATED)
        for dirname, subdirs, files in os.walk(root_path + task["path"]):
            arcname = dirname[len_prefix:]
            zf.write(dirname, arcname)
            for filename in files:
                zf.write(os.path.join(dirname, filename), os.path.join(arcname, filename))
        zf.close()
        status = "success"
        result = zip_name + " created"
        edit_tasks(finish_task)
    except Exception as e:
        status = "error"
        result = str(e)
        edit_tasks(finish_task)

@app.route('/_zip/<path:path>')
def route_zip(path):
    task_id = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    def add_task(tasks):
        tasks[task_id] = {
            "id": task_id,
            "status": "waiting",
            "type": "zip",
            "path": clean_path(path, True),
            "result": None
        }
        return tasks
    edit_tasks(add_task)
    t = Thread(target=exec_task, args=(task_id,))
    t.start()
    return redirect(url_for('route_tasks'))

@app.route('/_remove/<path:path>')
def route_remove(path):
    path = clean_path(path)
    fullpath = root_path + path
    try:
        if path == "/":
            raise Exception("Permission denied")
        if os.path.isdir(fullpath):
            from shutil import rmtree
            rmtree(fullpath, True)
            if path[-1] != "/":
                path += "/"
            path = os.path.dirname(path)
        else:
            os.remove(fullpath)
    except Exception as e:
        print(e)
        return render_template('message.html', message="Impossible to remove the file")
    return redirect(os.path.dirname(path) + "/")

@app.route('/_tasks/')
def route_tasks():
    for root, dirs, files in os.walk("/tmp/toto/"):
        print("root=", root)
        print("dirs=", dirs)
        print("files=", files)
    return render_template("tasks.html", tasks=get_tasks())

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
