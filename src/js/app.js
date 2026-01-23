// ========================================
// MOCK DATA
// ========================================

const MOCK_PROJECTS = [
    { id: 1, name: 'Website Redesign', description: 'Overhaul company website with new branding', status: 'active' },
    { id: 2, name: 'Mobile App Launch', description: 'Ship iOS and Android apps to production', status: 'active' },
    { id: 3, name: 'API Documentation', description: 'Complete API docs for external developers', status: 'active' }
];

const MOCK_TASKS = {
    1: {
        incomplete: [
            { id: 1, title: 'Design homepage mockup' },
            { id: 2, title: 'Update color palette' },
            { id: 3, title: 'Create component library' }
        ],
        completed: [
            { id: 4, title: 'Research competitor sites' },
            { id: 5, title: 'Gather stakeholder feedback' }
        ]
    },
    2: {
        incomplete: [
            { id: 6, title: 'Set up CI/CD pipeline' },
            { id: 7, title: 'Test on iOS devices' },
            { id: 8, title: 'Submit to App Store' }
        ],
        completed: [
            { id: 9, title: 'Build authentication flow' },
            { id: 10, title: 'Implement push notifications' }
        ]
    },
    3: {
        incomplete: [
            { id: 11, title: 'Document REST endpoints' },
            { id: 12, title: 'Add code examples' },
            { id: 13, title: 'Review with engineering team' }
        ],
        completed: [
            { id: 14, title: 'Set up documentation site' },
            { id: 15, title: 'Write authentication guide' }
        ]
    }
};

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

function TaskItem(task, isCompleted = false) {
    const item = document.createElement('div');
    item.className = isCompleted ? 'task-item task-completed' : 'task-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = isCompleted;
    checkbox.disabled = true; // No interaction on Day 3
    
    const title = document.createElement('span');
    title.textContent = task.title;
    
    item.appendChild(checkbox);
    item.appendChild(title);
    
    return item;
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
        const container = document.createElement('div');
        container.className = 'view-project-detail';
        
        // Find project
        const project = MOCK_PROJECTS.find(p => p.id == params.id);
        if (!project) {
            container.innerHTML = '<p>Project not found</p>';
            return container;
        }
        
        // Back link
        const backLink = document.createElement('a');
        backLink.href = '#/projects';
        backLink.className = 'back-link';
        backLink.textContent = '← Back to Projects';
        container.appendChild(backLink);
        
        // Project header
        const header = document.createElement('div');
        header.className = 'project-header';
        
        const name = document.createElement('h1');
        name.textContent = project.name;
        
        const description = document.createElement('p');
        description.textContent = project.description;
        
        header.appendChild(name);
        header.appendChild(description);
        container.appendChild(header);
        
        // Get tasks for this project
        const tasks = MOCK_TASKS[params.id] || { incomplete: [], completed: [] };
        
        // Incomplete tasks section
        const incompleteSection = document.createElement('div');
        incompleteSection.className = 'task-section';
        
        const incompleteHeading = document.createElement('h2');
        incompleteHeading.textContent = 'Incomplete';
        incompleteSection.appendChild(incompleteHeading);
        
        const incompleteList = document.createElement('div');
        incompleteList.className = 'task-list';
        tasks.incomplete.forEach(task => {
            incompleteList.appendChild(TaskItem(task, false));
        });
        incompleteSection.appendChild(incompleteList);
        container.appendChild(incompleteSection);
        
        // Completed tasks section
        const completedSection = document.createElement('div');
        completedSection.className = 'task-section';
        
        const completedHeading = document.createElement('h2');
        completedHeading.textContent = 'Completed';
        completedSection.appendChild(completedHeading);
        
        const completedList = document.createElement('div');
        completedList.className = 'task-list';
        tasks.completed.forEach(task => {
            completedList.appendChild(TaskItem(task, true));
        });
        completedSection.appendChild(completedList);
        container.appendChild(completedSection);
        
        return container;
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
