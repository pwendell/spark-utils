name := "Spark Release Auditor"

version := "1.0"

scalaVersion := "2.9.3"

libraryDependencies += "org.apache.spark" % System.getenv.get("SPARK_MODULE") % System.getenv.get("SPARK_VERSION")

// See here: http://stackoverflow.com/questions/9889674/sbt-jetty-and-servlet-3-0

classpathTypes ~= (_ + "orbit")

libraryDependencies ++= Seq(
  "org.eclipse.jetty.orbit" % "javax.servlet" % "3.0.0.v201112011016" % "compile" artifacts (Artifact("javax.servlet", "jar", "jar")
  )
)

libraryDependencies ++= Seq(
  "org.eclipse.jetty" % "jetty-webapp" % "8.1.4.v20120524" % "compile" artifacts (Artifact("jetty-webapp", "jar", "jar"))
)

resolvers ++= Seq(
  "Spark Release Repository" at System.getenv.get("SPARK_RELEASE_REPOSITORY"),
  "Akka Repository" at "http://repo.akka.io/releases/",
  "Spray Repository" at "http://repo.spray.cc/")
