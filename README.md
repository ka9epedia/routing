Okayama Routing
====

## Demo
Depending on input, the output is displayed as the result like the image below.
![result](https://github.com/ka9epedia/routing/media/routing.gif)

## Requirement
- Node.js and npm
- PosgreSQL,PostGIS and pgRouting

## Install

## Usage
Please edit config.js file  
app/config/config.js 

    database: {
      host: process.env.DATABASE_HOST || "database_host(localhost)",
      username: process.env.DATABASE_USER || "database_user",
      password: process.env.DATABASE_PASSWORD || "database_password",
      dbname: process.env.DATABASE_NAME || 'database_name'
    },

## Database
    psql -U username -d dbname
    CREATE EXTENSION postgis;
    CREATE EXTENSION pgrouting;
You can install the sample data or download your own from [OpenStreetMap](https://www.openstreetmap.org/#map=14/34.6637/133.9112)

    osm2pgrouting -file "okayama.osm" \
    -conf "/usr/share/osm2pgrouting/mapconfig.xml" \
    -dbname DBNAME \
    -user USERNAME \
    -clean

## Run
    npm install
    npm start
With the default settings, your server will be running at http://localhost:5050
## Author

[ka9epedia](https://github.com/ka9epedia)

