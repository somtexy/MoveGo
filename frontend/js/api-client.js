
/**
 * MoveGo Django API Client
 * Uses same-origin requests and Django session cookies.
 */

const MoveGoAPI = (() => {
    async function getCsrfToken() {
        const response = await fetch("/api/auth/csrf/", {
            method: "GET",
            credentials: "same-origin"
        });

        if (!response.ok) {
            throw new Error("Unable to obtain CSRF token.");
        }

        const data = await response.json();
        return data.csrfToken;
    }

    async function request(endpoint, options = {}) {
        const method = (options.method || "GET").toUpperCase();

        const headers = {
            "Accept": "application/json",
            ...options.headers
        };

        if (options.body != null && !(options.body instanceof FormData)) {
            headers["Content-Type"] = "application/json";
        }

        if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
            headers["X-CSRFToken"] = await getCsrfToken();
        }

        const response = await fetch(endpoint, {
            ...options,
            method,
            headers,
            credentials: "same-origin"
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(
                data?.error ||
                data?.detail ||
                data?.message ||
                `Request failed (${response.status})`
            );
        }

        return data;
    }

    return {
        getCsrfToken,

        getProfile() {
            return request("/api/auth/me/");
        },

        login(email, password) {
            return request("/api/auth/login/", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });
        },

        register(userData) {
            return request("/api/auth/register/", {
                method: "POST",
                body: JSON.stringify(userData)
            });
        },

        logout() {
            return request("/api/auth/logout/", {
                method: "POST",
                body: JSON.stringify({})
            });
        }
    };
})();

window.MoveGoAPI = MoveGoAPI;
