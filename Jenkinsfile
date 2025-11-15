pipeline {
  agent any

  environment {
    AEGIS_API_KEY = ""
    CONFIG_API_URL = ""
  }

  options {
    timeout(time: 60, unit: 'MINUTES')
    ansiColor('xterm')
  }

  stages {
    stage('Set up Docker Buildx') {
      steps {
        sh 'docker buildx version || (docker buildx create --use && docker buildx version) || true'
      }
    }

    stage('Run Security Scan (Docker)') {
      steps {
        withCredentials([
          string(credentialsId: 'aegis_api_key', variable: 'AEGIS_API_KEY'),
          string(credentialsId: 'config_api_url', variable: 'CONFIG_API_URL')
        ]) {
          sh '''
            set -euo pipefail
            mkdir -p results
            echo "Pulling Aegis image..."
            docker pull playerunknown23/aegis:latest || true
            echo "Running Aegis scanner container..."
            SCANNER_EXIT=0
            if [ -n "${CONFIG_API_URL:-}" ]; then
              CONFIG_ARG="--config-api-url=${CONFIG_API_URL}"
            else
              CONFIG_ARG=""
            fi
            docker run --rm \
              -v "${WORKSPACE}:/app/target:ro" \
              -v "${WORKSPACE}/results:/app/results:rw" \
              -e AEGIS_API_KEY="${AEGIS_API_KEY}" \
              -e CONFIG_API_URL="${CONFIG_API_URL}" \
              -e GITHUB_REPOSITORY="${JOB_NAME}" \
              -e GITHUB_REF="${BRANCH_NAME:-unknown-ref}" \
              -e GITHUB_SHA="${GIT_COMMIT:-unknown-sha}" \
              playerunknown23/aegis:latest \
              /app/target \
              --api-key "${AEGIS_API_KEY}" \
              ${CONFIG_ARG} \
              --parallel || SCANNER_EXIT=$?
            echo "Aegis exit code: $SCANNER_EXIT"
            exit $SCANNER_EXIT
          '''
        }
      }
    }
  }
}

