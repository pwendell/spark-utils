name := "Spark Release Auditor"

version := "1.0"

scalaVersion := "2.9.3"

libraryDependencies += "org.apache.spark" % System.getenv.get("SPARK_MODULE") % System.getenv.get("SPARK_VERSION")

resolvers ++= Seq(
  "Spark Release Repository" at System.getenv.get("SPARK_RELEASE_REPOSITORY"),
  "Akka Repository" at "http://repo.akka.io/releases/",
  "Spray Repository" at "http://repo.spray.cc/")
