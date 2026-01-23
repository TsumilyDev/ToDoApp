// ========================================
// MOCK DATA
// ========================================

const MOCK_PROJECTS = [
    { id: 1, name: 'Website Redesign', description: 'Overhaul company website with new branding', status: 'active' },
    { id: 2, name: 'Mobile App Launch', description: 'Ship iOS and Android apps to production', status: 'active' },
    { id: 3, name: 'API Documentation', description: 'Complete API docs for external developers', status: 'active' }
];

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
            // Clear view
            view.innerHTML = '';
            
            // Render view (may return string or DOM element)
            const content = matched.handler(matched.params);
            
            if (typeof content === 'string') {
                view.innerHTML = content;
            } else {
                view.appendChild(content);
            }
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
// COMPONENTS
// ========================================

function ProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'project-card';
    
    const name = document.createElement('h3');
    name.textContent = project.name;
    
    const description = document.createElement('p');
    description.textContent = project.description;
    
    card.appendChild(name);
    card.appendChild(description);
    
    // Make card clickable
    card.addEventListener('click', () => {
        window.location.hash = `#/projects/${project.id}`;
    });
    
    return card;
}

// ========================================
// VIEWS
// ========================================

const views = {
    projects: () => {
        const container = document.createElement('div');
        container.className = 'view-projects';
        
        const heading = document.createElement('h1');
        heading.textContent = 'Projects';
        container.appendChild(heading);
        
        // Filter active projects only
        const activeProjects = MOCK_PROJECTS.filter(p => p.status === 'active');
        
        const projectList = document.createElement('div');
        projectList.className = 'project-list';
        
        activeProjects.forEach(project => {
            projectList.appendChild(ProjectCard(project));
        });
        
        container.appendChild(projectList);
        
        return container;
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
