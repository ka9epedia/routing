Okayama Routing
====

## Demo
![Demo](https://user-images.githubusercontent.com/42766115/47839268-7c7b9500-ddf5-11e8-87d5-5cf1b6c74636.gif)


## Requirement
- Node.js and npm
- PosgreSQL,PostGIS and pgRouting

## Buidl and Install 
pgRouting https://github.com/pgRouting/pgrouting  
osm2pgrouting https://github.com/pgRouting/osm2pgrouting  
    
    mkdir build
    cd build
    cmake ../
    make
    sudo make install

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
    node server.js
With the default settings, your server will be running at http://localhost:5050
## Author

[ka9epedia](https://github.com/ka9epedia)

