pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "lsstts/love-producer:"
    dockerImage = ""
    dockerLoveCSCImageName = "lsstts/love-csc:"
    dev_cycle = "c0020.001"
    user_ci = credentials('lsst-io')
    LTD_USERNAME="${user_ci_USR}"
    LTD_PASSWORD="${user_ci_PSW}"
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
          branch "tickets/*"
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
            if (git_branch == "release" || git_branch == "hotfix" || git_branch == "bugfix" || git_branch == "tickets") {
              image_tag = git_tag
            }
          }
          dockerImageName = dockerImageName + image_tag
          echo "dockerImageName: ${dockerImageName}"
          dockerImage = docker.build(dockerImageName, "--build-arg dev_cycle=${dev_cycle} .")
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
            branch "tickets/*"
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
            if (git_branch == "release" || git_branch == "hotfix" || git_branch == "bugfix" || git_branch == "tickets") {
              image_tag = git_tag
            }
          }
          dockerLoveCSCImageName = dockerLoveCSCImageName + image_tag
          echo "dockerLoveCSCImageName: ${dockerLoveCSCImageName}"
          dockerLoveCSCImageName = docker.build(dockerLoveCSCImageName, "--build-arg dev_cycle=${dev_cycle} -f ./Dockerfile-lovecsc .")
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
          branch "tickets/*"
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
          branch "test_pipeline"
        }
      }
      steps {
        script {
          sh "docker run lsstts/love-producer:develop /usr/src/love/producer/run-tests.sh"	
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
            branch "tickets/*"
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

    stage("Deploy documentation") {
      agent {
        docker {
          alwaysPull true
          image 'lsstts/develop-env:develop'
          args "-u root --entrypoint=''"
        }
      }
      when {
        anyOf {
          changeset "docs/*"
        }
      }
      steps {
        script {
          sh "pwd"
          sh """
            source /home/saluser/.setup_dev.sh
            pip install ltd-conveyor
            ltd upload --product love-producer --git-ref ${GIT_BRANCH} --dir ./docs
          """
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
