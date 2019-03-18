pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "inriachile/love-producer:${GIT_BRANCH}"
    dockerImage = ""
  }

  stages {
    stage("Build Docker image") {
      when {
        anyOf {
          branch "master"
          branch "develop"
        }
      }
      steps {
        script {
          dockerImage = docker.build(dockerImageName, "./telemetry-producer")
        }
      }
    }
    stage("Push Docker image") {
      when {
        anyOf {
          branch "master"
          branch "develop"
        }
      }
      steps {
        script {
          docker.withRegistry("", registryCredential) {
            dockerImage.push()
          }
        }
      }
    }
  }
}
