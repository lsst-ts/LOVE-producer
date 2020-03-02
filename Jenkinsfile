pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "lsstts/love-producer:"
    dockerImage = ""
    dockerLoveCSCImageName = "lsstts/love-csc:"
  }

  stages {
    stage("Build Producer Docker image") {
      when {
        anyOf {
          branch "master"
          branch "develop"
          branch "bugfix/*"
          branch "hotfix/*"
          branch "release/*"
        }
      }
      steps {
        script {
          def git_branch = "${GIT_BRANCH}"
          def image_tag = git_branch
          def slashPosition = git_branch.indexOf('/')
          if (slashPosition > 0) {
            git_tag = git_branch.substring(slashPosition + 1, git_branch.length())
            git_branch = git_branch.substring(0, slashPosition)
            if (git_branch == "release" || git_branch == "hotfix" || git_branch == "bugfix") {
              image_tag = git_tag
            }
          }
          dockerImageName = dockerImageName + image_tag
          echo "dockerImageName: ${dockerImageName}"
          dockerImage = docker.build dockerImageName
        }
      }
    }

    stage("Build LOVE-CSC Docker image") {
      when {
        allOf {
          anyOf {
            branch "master"
            branch "develop"
            branch "bugfix/*"
            branch "hotfix/*"
            branch "release/*"
          }
          anyOf {
            changeset "producer/love_csc/**/*"
            changeset "Jenkinsfile"
            triggeredBy "UpstreamCause"
            triggeredBy "UserIdCause"
          }
        }
      }
      steps {
        script {
          def git_branch = "${GIT_BRANCH}"
          def image_tag = git_branch
          def slashPosition = git_branch.indexOf('/')
          if (slashPosition > 0) {
            git_tag = git_branch.substring(slashPosition + 1, git_branch.length())
            git_branch = git_branch.substring(0, slashPosition)
            if (git_branch == "release" || git_branch == "hotfix" || git_branch == "bugfix") {
              image_tag = git_tag
            }
          }
          dockerLoveCSCImageName = dockerLoveCSCImageName + image_tag
          echo "dockerLoveCSCImageName: ${dockerLoveCSCImageName}"
          dockerLoveCSCImageName = docker.build(dockerLoveCSCImageName, "-f ./Dockerfile-lovecsc .")
        }
      }
    }

    stage("Push Docker image") {
      when {
        anyOf {
          branch "master"
          branch "develop"
          branch "bugfix/*"
          branch "hotfix/*"
          branch "release/*"
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

    stage("Run tests") {
      when {
        anyOf {
          branch "develop"
        }
      }
      steps {
        script {
          sh "docker run ${dockerImageName} /usr/src/love/producer/run-tests.sh"	
        }
      }
    }

    stage("Push LOVE-CSC Docker image") {
      when {
        allOf {
          anyOf {
            branch "master"
            branch "develop"
            branch "bugfix/*"
            branch "hotfix/*"
            branch "release/*"
          }
          anyOf {
            changeset "producer/love_csc/**/*"
            changeset "Jenkinsfile"
            triggeredBy "UpstreamCause"
            triggeredBy "UserIdCause"
          }
        }
      }
      steps {
        script {
          docker.withRegistry("", registryCredential) {
            dockerLoveCSCImageName.push()
          }
        }
      }
    }

    stage("Trigger develop deployment") {
      when {
        branch "develop"
      }
      steps {
        build(job: '../LOVE-integration-tools/develop', wait: false)
      }
    }
    stage("Trigger master deployment") {
      when {
        branch "master"
      }
      steps {
        build(job: '../LOVE-integration-tools/master', wait: false)
      }
    }
  }
}
