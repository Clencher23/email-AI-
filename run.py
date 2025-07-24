
# from flask import Flask, render_template, session, redirect, jsonify
# from apps.routes.auth import auth_bp
# from apps.routes.emails import emails_bp
# from config import Config
# import os

# def create_app():
#     app = Flask(__name__, template_folder=r"E:\email-agent-AI\apps\templates")
#     app.config.from_object(Config)


#     app.secret_key = "a3b27f9c2eac49f6941f61b6f2d41f9a32d4ee28b6cf3f62ff28a90d6c27df90"

#     @app.route("/")
#     def login():
#         return jsonify(emails)
        

#     # @app.route("/emails/list")
#     # def inbox():
#     #     return render_template("emails.html")

#     @app.route("/emailai.html")
#     def email_ui():
#         if 'user_id' not in session:
#             return redirect("/")
        
#         return render_template("emailai.html")
#           # this is the inbox UI
    
    


#         # Register Blueprints
#     app.register_blueprint(auth_bp, url_prefix="/auth")
#     app.register_blueprint(emails_bp, url_prefix="/emails")
#     # app.register_blueprint(attachments_bp, url_prefix="/attachments")

#     # Create attachments folder if it doesn't exist
#     os.makedirs(app.config["ATTACHMENTS_DIR"], exist_ok=True)

#     return app

# if __name__ == "__main__":
#     app = create_app()
#     app.run(debug=True, host="0.0.0.0")

from flask import Flask, render_template, session, redirect, send_from_directory
from apps.routes.auth import auth_bp
from apps.routes.emails import emails_bp
from config import Config
from apps.routes.auth import set_app_instance
import os

def create_app():
    app = Flask(__name__, template_folder=r"C:\Users\Aman Rajwanshi\Downloads\email-ai-main-2\apps\templates")
    app.config.from_object(Config)

    app.secret_key = "a3b27f9c2eac49f6941f61b6f2d41f9a32d4ee28b6cf3f62ff28a90d6c27df90"

    #  Login page route
    @app.route("/")
    def login():
        if "user_id" in session:
            return redirect("/emails.html")

        return render_template("login.html")

    #  Inbox UI route
    @app.route("/emails.html")
    def email_ui():
        if 'user_id' not in session:
            return redirect("/")
        return render_template("emails.html")
    
    @app.route("/download/<filename>")
    def download_attachment(filename):
        return send_from_directory(Config.ATTACHMENTS_DIR, filename, as_attachment=True)


    #  Register Blueprints (indentation fixed)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(emails_bp, url_prefix="/emails")

   

    return app

app = create_app()
set_app_instance(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
