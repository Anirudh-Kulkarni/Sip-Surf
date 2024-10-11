# Install required packages
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap5

# Define Flask app
app = Flask(__name__)
# Use app.config['SECRET_KEY'] . This is highly recommended.
Bootstrap5(app)


# Declare database base class.
class Base(DeclarativeBase):
    pass


# Configure database .
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[str] = mapped_column(String(250), nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Create database
with app.app_context():
    db.create_all()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Api docs page
@app.route("/api-docs")
def api_docs():
    return render_template("api_docs.html")


# Page listing all cafes
@app.route('/cafes')
def cafes():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    cafes_dict = [cafe.to_dict() for cafe in all_cafes]
    return render_template('cafes.html', cafes=cafes_dict)


# Page to add a new cafe
@app.route('/add', methods=["GET", "POST"])
def add_cafe():
    if request.method == 'POST':
        name = request.form['name']
        map_url = request.form['map_url']
        img_url = request.form['img_url']
        location = request.form['location']
        seats = request.form['seats']
        has_toilet = bool(request.form['has_toilet'])
        has_wifi = bool(request.form['has_wifi'])
        has_sockets = request.form['has_sockets']
        can_take_calls = bool(request.form['can_take_calls'])
        coffee_price = request.form['coffee_price']

        new_cafe = Cafe(name=name, map_url=map_url, img_url=img_url,
                        location=location, seats=seats, has_toilet=has_toilet, has_wifi=has_wifi,
                        has_sockets=has_sockets, can_take_calls=can_take_calls, coffee_price=coffee_price)

        db.session.add(new_cafe)
        db.session.commit()
        # Save to the database...

        return redirect(url_for('cafes'))
    return render_template('add.html')


# Search for a cafe
@app.route("/search", methods=["GET", "POST"])
def get_cafe_at_location():
    if request.method == 'POST':
        query_location = request.form.get("search_loc")
        print(str.title(query_location))
        result = db.session.execute(db.select(Cafe).where(Cafe.location == str.title(query_location)))
        # Note, this may get more than one cafe per location
        all_cafes = result.scalars().all()
        cafes_dict = [cafe.to_dict() for cafe in all_cafes]
        return render_template('cafes.html', cafes=cafes_dict)
    return render_template('cafes.html')


# API function - to add a cafe
@app.route("/api/add", methods=["POST"])
def api_post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("location"),
        has_sockets=bool(request.form.get("has_sockets")),
        has_toilet=bool(request.form.get("has_toilet")),
        has_wifi=bool(request.form.get("has_wifi")),
        can_take_calls=bool(request.form.get("can_take_calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


# API function - to list all cafes
@app.route("/api/all")
def api_get_all_cafes():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


# API function - to update the price of a cafe
@app.route("/api/update-price/<int:cafe_id>", methods=["PATCH"])
def api_patch_new_price(cafe_id):
    new_price = request.args.get("new_price")
    cafe = db.get_or_404(Cafe, cafe_id)
    if cafe:
        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."}), 200
    else:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404


# API function - to delete a cafe
@app.route("/api/report-closed/<int:cafe_id>", methods=["DELETE"])
def api_delete_cafe(cafe_id):
    api_key = request.args.get("api-key")
    if api_key == "TopSecretAPIKey":
        cafe = db.get_or_404(Cafe, cafe_id)
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403


# API function - to search a cafe at a location
@app.route("/api/search")
def api_get_cafe_at_location():
    query_location = request.args.get("location")
    result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location))
    # Note, this may get more than one cafe per location
    all_cafes = result.scalars().all()
    if all_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404


if __name__ == '__main__':
    app.run(debug=True)
