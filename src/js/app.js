// ========================================
// ROUTER
// ========================================

class Router {
    constructor(routes) {
        this.routes = routes;
        this.init();
    }

    init() {
        // Listen for hash changes
        window.addEventListener('hashchange', () => this.route());
        
        // Handle initial load
        window.addEventListener('load', () => this.route());
    }

    route() {
        const hash = window.location.hash.slice(1) || '/projects'; // Default to /projects
        const view = document.getElementById('app-view');

        // Match route
        const matched = this.matchRoute(hash);

        if (matched) {
            view.innerHTML = matched.handler(matched.params);
        } else {
            // Fallback to projects
            window.location.hash = '#/projects';
        }
    }

    matchRoute(hash) {
        for (let route of this.routes) {
            const params = this.extractParams(route.path, hash);
            if (params !== null) {
                return { handler: route.handler, params };
            }
        }
        return null;
    }

    extractParams(routePath, hash) {
        const routeParts = routePath.split('/');
        const hashParts = hash.split('/');

        if (routeParts.length !== hashParts.length) {
            return null;
        }

        const params = {};
        for (let i = 0; i < routeParts.length; i++) {
            if (routeParts[i].startsWith(':')) {
                // Dynamic segment
                const paramName = routeParts[i].slice(1);
                params[paramName] = hashParts[i];
            } else if (routeParts[i] !== hashParts[i]) {
                // Segments don't match
                return null;
            }
        }
        return params;
    }
}

// ========================================
// VIEWS (Placeholders)
// ========================================

const views = {
    projects: () => {
        return `
            <div class="view-projects">
                <h1>Projects</h1>
                <p>Project list will go here</p>
            </div>
        `;
    },

    projectDetail: (params) => {
        return `
            <div class="view-project-detail">
                <h1>Project: ${params.id}</h1>
                <p>Project overview will go here</p>
                <a href="#/projects">← Back to Projects</a>
            </div>
        `;
    },

    info: () => {
        return `
            <div class="view-info">
                <h1>Info</h1>
                <p>Info page will go here</p>
            </div>
        `;
    }
};

// ========================================
// ROUTE CONFIGURATION
// ========================================

const routes = [
    { path: '/projects/:id', handler: views.projectDetail },
    { path: '/projects', handler: views.projects },
    { path: '/info', handler: views.info }
];

// ========================================
// INITIALIZE APP
// ========================================

const app = new Router(routes);
