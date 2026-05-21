#!/usr/bin/env bash
set -euo pipefail

APP_NAME="mywebapp"
APP_USER="mywebapp"
APP_GROUP="mywebapp"
APP_ROOT="/opt/${APP_NAME}"
APP_CURRENT="${APP_ROOT}/current"
APP_VENV="${APP_ROOT}/venv"
SYSTEMD_DIR="/etc/systemd/system"
NGINX_SITE="/etc/nginx/sites-available/${APP_NAME}.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/${APP_NAME}.conf"
ENV_FILE="/etc/default/${APP_NAME}"
SUDOERS_FILE="/etc/sudoers.d/operator-${APP_NAME}"
GRADEBOOK_FILE="/home/student/gradebook"

DEFAULT_VM_USER="${DEFAULT_VM_USER:-korzunz}"
STUDENT_PASSWORD="${STUDENT_PASSWORD:-12345678}"
TEACHER_PASSWORD="${TEACHER_PASSWORD:-12345678}"
OPERATOR_PASSWORD="${OPERATOR_PASSWORD:-12345678}"
DB_NAME="${DB_NAME:-mywebapp}"
DB_USER="${DB_USER:-mywebapp}"
DB_PASSWORD="${DB_PASSWORD:-mywebapp-secret}"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-3000}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
GRADEBOOK_NUMBER="${GRADEBOOK_NUMBER:-2}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "Run this installer as root." >&2
        exit 1
    fi
}

install_packages() {
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y python3 python3-venv python3-pip mariadb-server nginx sudo curl git
}

ensure_user() {
    local username="$1"
    local shell_path="$2"
    if ! id -u "${username}" >/dev/null 2>&1; then
        useradd --create-home --shell "${shell_path}" "${username}"
    fi
}

configure_password() {
    local username="$1"
    local password="$2"
    printf '%s:%s\n' "${username}" "${password}" | chpasswd
    chage -d 0 "${username}"
}

prepare_users() {
    ensure_user "student" "/bin/bash"
    ensure_user "teacher" "/bin/bash"
    if ! getent group operator >/dev/null 2>&1; then
        groupadd operator
    fi
    if ! id -u operator >/dev/null 2>&1; then
        useradd --create-home --shell /bin/bash -g operator operator
    fi
    if ! getent group "${APP_GROUP}" >/dev/null 2>&1; then
        groupadd --system "${APP_GROUP}"
    fi
    if ! id -u "${APP_USER}" >/dev/null 2>&1; then
        useradd --system --gid "${APP_GROUP}" --home "${APP_ROOT}" --shell /usr/sbin/nologin "${APP_USER}"
    fi

    configure_password "student" "${STUDENT_PASSWORD}"
    configure_password "teacher" "${TEACHER_PASSWORD}"
    configure_password "operator" "${OPERATOR_PASSWORD}"

    usermod -aG sudo student
    usermod -aG sudo teacher
}

prepare_application_tree() {
    install -d -o "${APP_USER}" -g "${APP_GROUP}" "${APP_ROOT}" "${APP_CURRENT}"
    rm -rf "${APP_CURRENT}/mywebapp" "${APP_CURRENT}/scripts" "${APP_CURRENT}/tests"
    cp -r "${REPO_ROOT}/mywebapp" "${APP_CURRENT}/"
    cp -r "${REPO_ROOT}/scripts" "${APP_CURRENT}/"
    cp -r "${REPO_ROOT}/tests" "${APP_CURRENT}/"
    cp "${REPO_ROOT}/requirements.txt" "${APP_CURRENT}/"
    chown -R "${APP_USER}:${APP_GROUP}" "${APP_ROOT}"
}

prepare_virtualenv() {
    python3 -m venv "${APP_VENV}"
    "${APP_VENV}/bin/pip" install --upgrade pip
    "${APP_VENV}/bin/pip" install -r "${APP_CURRENT}/requirements.txt"
}

prepare_database() {
    systemctl enable --now mariadb
    mysql <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL
}

write_env_file() {
    cat > "${ENV_FILE}" <<EOF
MYWEBAPP_HOST=${APP_HOST}
MYWEBAPP_PORT=${APP_PORT}
MYWEBAPP_DB_HOST=${DB_HOST}
MYWEBAPP_DB_PORT=${DB_PORT}
MYWEBAPP_DB_NAME=${DB_NAME}
MYWEBAPP_DB_USER=${DB_USER}
MYWEBAPP_DB_PASSWORD=${DB_PASSWORD}
EOF
    chmod 640 "${ENV_FILE}"
    chown root:"${APP_GROUP}" "${ENV_FILE}"
}

install_systemd_units() {
    install -m 644 "${REPO_ROOT}/deploy/mywebapp.service" "${SYSTEMD_DIR}/mywebapp.service"
    install -m 644 "${REPO_ROOT}/deploy/mywebapp.socket" "${SYSTEMD_DIR}/mywebapp.socket"
    systemctl daemon-reload
    systemctl enable mywebapp.socket
    systemctl restart mywebapp.socket
    curl --silent --show-error --fail "http://${APP_HOST}:${APP_PORT}/health/alive" >/dev/null
}

install_nginx() {
    install -m 644 "${REPO_ROOT}/deploy/nginx-mywebapp.conf" "${NGINX_SITE}"
    ln -sfn "${NGINX_SITE}" "${NGINX_ENABLED}"
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl enable --now nginx
    systemctl reload nginx
}

install_operator_sudoers() {
    install -m 440 "${REPO_ROOT}/deploy/operator-mywebapp.sudoers" "${SUDOERS_FILE}"
    visudo -cf "${SUDOERS_FILE}"
}

write_gradebook() {
    printf '%s\n' "${GRADEBOOK_NUMBER}" > "${GRADEBOOK_FILE}"
    chown student:student "${GRADEBOOK_FILE}"
    chmod 644 "${GRADEBOOK_FILE}"
}

disable_default_user() {
    if id -u "${DEFAULT_VM_USER}" >/dev/null 2>&1; then
        passwd -l "${DEFAULT_VM_USER}"
    fi
}

main() {
    require_root
    install_packages
    prepare_users
    prepare_application_tree
    prepare_virtualenv
    prepare_database
    write_env_file
    install_systemd_units
    install_nginx
    install_operator_sudoers
    write_gradebook
    disable_default_user
    echo "Deployment completed successfully."
}

main "$@"
