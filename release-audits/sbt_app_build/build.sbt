name := "Simple Project"

version := "1.0"

scalaVersion := "2.9.3"

libraryDependencies += "org.apache.spark" %% "spark-core" % System.getenv.get("SPARK_VERSION")

resolvers ++= Seq(
  "Spark Release Repository" at System.getenv.get("SPARK_RELEASE_REPOSITORY"),
  "Akka Repository" at "http://repo.akka.io/releases/",
  "Spray Repository" at "http://repo.spray.cc/")
