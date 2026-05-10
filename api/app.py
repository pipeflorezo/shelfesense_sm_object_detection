import settings
from flask import Flask
import utils

from werkzeug.utils import secure_filename
import os
from middleware import model_detect

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = settings.UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = settings.PROCESSED_FOLDER
app.secret_key = "shelfsense"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files["file"]
    if file.filename == "":
        flash("No image selected for uploading")
        return redirect(request.url)

    if file and utils.allowed_file(file.filename):

        hash_imgname = utils.get_file_hash(file)
        img_savepath = os.path.join(settings.UPLOAD_FOLDER, hash_imgname)

        if not os.path.exists(img_savepath):
            file.stream.seek(0)
            file.save(img_savepath)
            if not utils.verify_image(img_savepath):
                os.remove(img_savepath)
                flash("Image is corrupted, try with another one")
                return redirect(request.url)

        detection_dict = model_detect(hash_imgname)

        alpha = 0.5
        utils.draw_mask(detection_dict["bouding_boxes"], hash_imgname, alpha)

        return render_template("index.html", filename=hash_imgname)

    else:
        flash("Allowed image types are -> png, jpg, jpeg, gif")
        return redirect(request.url)


@app.route("/display/<filename>")
def display_image(filename):
    return redirect(url_for("static", filename="uploads/" + filename), code=301)


@app.route("/display/processed/<filename>")
def display_image_processed(filename):
    return redirect(url_for("static", filename="processed/" + filename), code=301)


@app.route("/detect", methods=["POST"])
def detect():
    if "file" not in request.files:
        rpse = {"success": False, "detections": None}
        return jsonify(rpse), 400

    file = request.files["file"]
    if file.filename == "":
        rpse = {"success": False, "detections": None}
        return jsonify(rpse), 400

    if file and utils.allowed_file(file.filename):
        file.filename = utils.get_file_hash(file)
        image_full_path = os.path.join(
            settings.UPLOAD_FOLDER, secure_filename(file.filename)
        )
        if not os.path.exists(image_full_path):
            file.save(image_full_path)
            if not utils.verify_image(image_full_path):
                os.remove(image_full_path)
                rpse = {"success": False, "detections": None}
                return jsonify(rpse), 400

        detection_dict_tmp = model_detect(file.filename)

        rpse = {"success": True, "detections": {"Data": detection_dict_tmp}}
        return jsonify(rpse), 200
    else:
        rpse = {"success": False, "detections": None}
        return jsonify(rpse), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=settings.API_DEBUG)
