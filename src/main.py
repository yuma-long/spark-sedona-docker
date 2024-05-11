import os
from pyspark.sql.functions import expr
from pyspark.sql.session import SparkSession
from sedona.spark import SedonaContext
from sedona.sql.st_predicates import ST_Intersects


def main():

    # 1. Download GeoJSON
    os.makedirs("src/input", exist_ok=True)

    state_url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/us-state-boundaries/exports/geojson?lang=en&timezone=Asia%2FTokyo"
    county_url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/us-county-boundaries/exports/geojson?lang=en&timezone=Asia%2FTokyo"

    state_geojson = "src/input/state.geojson"
    county_geojson = "src/input/county.geojson"

    for url, filename in zip([state_url, county_url], [state_geojson, county_geojson]):
        if not os.path.exists(filename):
            os.system(f"curl -o {filename} {url}")

    # 2. Spark Configuration
    print("Spark Configuraiton")
    config = SparkSession(
        SedonaContext.builder()
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .config(
            "spark.jars.packages",
            "org.apache.sedona:sedona-spark-3.5_2.12:1.5.1,"  # Sedona のパッケージ
            "org.datasyslab:geotools-wrapper:1.5.1-28.2",  # GeoTools のパッケージ
        )
        .master("local[*]")
        .getOrCreate()
    )

    spark = SedonaContext.create(config)

    # 3. Load GeoJSON to DataFrame
    schema = "type string, features array<struct<type string, geometry string, properties map<string, string>>>"

    dfreader = spark.read.schema(schema)

    df_state = (
        dfreader.json(state_geojson)
        .selectExpr("explode(features) as features")
        .select("features.*")
        .withColumn("geometry", expr("ST_GeomFromGeoJSON(geometry)"))
        .select("properties.name", "geometry")
        .withColumnRenamed("geometry", "state_geometry")
    )

    df_county = (
        dfreader.json(county_geojson)
        .selectExpr("explode(features) as features")
        .select("features.*")
        .withColumn("geometry", expr("ST_GeomFromGeoJSON(geometry)"))
        .select("properties.name", "geometry")
        .withColumnRenamed("geometry", "county_geometry")
    )

    # 4. Geometry Operation
    df_california = df_state.filter(df_state.name == "California")
    df_california = df_california.crossJoin(df_county)

    df_county_in_california = df_california.filter(
        ST_Intersects(df_california.state_geometry, df_california.county_geometry)
    )

    df_county_in_california.show()
    print(f"Count: {df_county_in_california.count()}")


if __name__ == "__main__":
    main()
