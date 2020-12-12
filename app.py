import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine,inspect, func
from flask import Flask, jsonify
import numpy as np
import pandas as pd

# create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite", echo=False)

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station     = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# Flask Setup
app = Flask(__name__)

@app.route("/")
def welcome():
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"  
        f"/api/v1.0/stations<br/>"  
        f"/api/v1.0/tobs<br/>" 
        f"/api/v1.0/<start><br/>" 
        f"/api/v1.0/<start>/<end><br/>" 
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    prcp_dictionary = {}
    prcp_last_twelve = engine.execute("Select prcp, date from Measurement where date >="
                                          "(Select strftime('%Y-%m-%d',max(m.date),'-12 month') from Measurement m)"
                                  "order by date desc"
                                 ).fetchall()   
    for data in prcp_last_twelve:
        #Convert the query results to a dictionary using date as the key and prcp as the value.
        prcp_dictionary[data[1]] = data[0]
   # Return the JSON representation of your dictionary.
    return jsonify(prcp_dictionary)


@app.route("/api/v1.0/stations")
def stations():
    station_dictionary = {}
    
    stations = session.query(Station.station, Station.name).distinct().all()
    for data in stations:
        station_dictionary[data[0]] = data[1]
    #Return a JSON list of stations from the dataset.
    return jsonify(station_dictionary)

@app.route("/api/v1.0/tobs")
def tobs():
    tobs_dictionary = {}

    #Query the dates and temperature observations of the most active station for the last year of data.
    temp_obs = engine.execute("Select mt.tobs, mt.date "
                          "from Measurement mt "
                          "where mt.station = 'USC00519281' "
                          "and mt.date >="
                                          "(Select strftime('%Y-%m-%d',max(m.date),'-12 month') "
                                             "from Measurement m "
                                            "where m.station = 'USC00519281' )"
                          "order by mt.date asc").fetchall()

    #Return a JSON list of temperature observations (TOBS) for the previous year.
    for data in temp_obs:
        tobs_dictionary[data[1]] = data[0]
    return jsonify(tobs_dictionary)


def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
       
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()


@app.route("/api/v1.0/<start>")

def tcalc_start(start):
    date_data_list = []
    date_max_func = engine.execute("Select strftime('%Y-%m-%d',max(m.date)) from Measurement m" ).fetchall()
    #date_max_func = session.query(func.max(func.strftime("%Y-%m-%d, Measurement.date"))).all()
    date_max = date_max_func[0][0]

    date_data = calc_temps(start,date_max)

    date_data_list = ({'MinimumTemperature':date_data[0][0]},
                      {'Average Temperature':date_data[0][1]},
                      {'Maximum Temperature':date_data[0][2]})
      
    return jsonify(date_data_list)

@app.route("/api/v1.0/<start>/<end>")

def tcalc_start_end(start,end):
    date_data_list_se = []
   
    date_data_se = calc_temps(start,end)

    date_data_list_se = ({'MinimumTemperature':date_data_se[0][0]},
                      {'Average Temperature':date_data_se[0][1]},
                      {'Maximum Temperature':date_data_se[0][2]})
      
    return jsonify(date_data_list_se)
 
if __name__ == "__main__":
    app.run(debug=True)