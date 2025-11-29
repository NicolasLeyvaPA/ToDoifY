/**
 * TaskFlow - Professional Task Management
 * Modern JavaScript with smooth interactions and animations
 */

const API = '/api';
let currentFilter = 'all';
let currentPriority = '';
let taskToDelete = null;

// DOM Elements
const elements = {
    sidebar: document.getElementById('sidebar'),
    menuBtn: document.getElementById('menu-btn'),
    themeToggle: document.getElementById('theme-toggle'),
    searchInput: document.getElementById('search'),
    filterBtn: document.getElementById('filter-btn'),
    newTaskBtn: document.getElementById('new-task-btn'),
    tasksContainer: document.getElementById('tasks-container'),
    emptyState: document.getElementById('empty-state'),
    taskModal: document.getElementById('task-modal'),
    deleteModal: document.getElementById('delete-modal'),
    taskForm: document.getElementById('task-form'),
    toastContainer: document.getElementById('toast-container'),
    sectionTitle: document.getElementById('section-title'),
    statusGroup: document.getElementById('status-group')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    loadTheme();
    loadTasks();
    loadStats();
    setupEventListeners();
    setupKeyboardShortcuts();
}

// Theme Management
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Event Listeners
function setupEventListeners() {
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // Mobile menu
    elements.menuBtn.addEventListener('click', () => {
        elements.sidebar.classList.toggle('open');
        toggleOverlay();
    });
    
    // New task button
    elements.newTaskBtn.addEventListener('click', () => openModal());
    
    // Form submission
    elements.taskForm.addEventListener('submit', handleFormSubmit);
    
    // Search with debounce
    let searchTimeout;
    elements.searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadTasks(), 300);
    });
    
    // Navigation filters
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            currentFilter = item.dataset.filter;
            updateSectionTitle();
            loadTasks();
        });
    });
    
    // Priority filter
    document.querySelectorAll('input[name="priority"]').forEach(input => {
        input.addEventListener('change', (e) => {
            currentPriority = e.target.value;
            loadTasks();
        });
    });
    
    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            elements.tasksContainer.className = btn.dataset.view === 'list' ? 'tasks-list' : 'tasks-grid';
        });
    });
    
    // Confirm delete
    document.getElementById('confirm-delete').addEventListener('click', confirmDelete);
    
    // Close modals on backdrop click
    [elements.taskModal, elements.deleteModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                if (modal === elements.taskModal) closeModal();
                else closeDeleteModal();
            }
        });
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + K for search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            elements.searchInput.focus();
        }
        // Escape to close modals
        if (e.key === 'Escape') {
            closeModal();
            closeDeleteModal();
        }
        // N for new task (when not in input)
        if (e.key === 'n' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            openModal();
        }
    });
}

function toggleOverlay() {
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', () => {
            elements.sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
        document.body.appendChild(overlay);
    }
    overlay.classList.toggle('active', elements.sidebar.classList.contains('open'));
}

function updateSectionTitle() {
    const titles = {
        'all': 'All Tasks',
        'pending': 'Pending Tasks',
        'in_progress': 'In Progress',
        'completed': 'Completed Tasks'
    };
    elements.sectionTitle.textContent = titles[currentFilter] || 'All Tasks';
}

// API Functions
async function loadTasks() {
    try {
        const params = new URLSearchParams();
        if (currentFilter !== 'all') params.append('status', currentFilter);
        if (currentPriority) params.append('priority', currentPriority);
        if (elements.searchInput.value.trim()) params.append('search', elements.searchInput.value.trim());
        
        const response = await fetch(`${API}/tasks?${params}`);
        const data = await response.json();
        renderTasks(data.tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
        showToast('Failed to load tasks', 'error');
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API}/stats`);
        const stats = await response.json();
        
        document.getElementById('total-tasks').textContent = stats.total_tasks;
        document.getElementById('pending-tasks').textContent = stats.by_status.pending;
        document.getElementById('in-progress-tasks').textContent = stats.by_status.in_progress;
        document.getElementById('completed-tasks').textContent = stats.by_status.completed;
        
        document.getElementById('nav-all-count').textContent = stats.total_tasks;
        document.getElementById('nav-pending-count').textContent = stats.by_status.pending;
        document.getElementById('nav-progress-count').textContent = stats.by_status.in_progress;
        document.getElementById('nav-completed-count').textContent = stats.by_status.completed;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function createTask(data) {
    const response = await fetch(`${API}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to create task');
    return response.json();
}

async function updateTask(id, data) {
    const response = await fetch(`${API}/tasks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to update task');
    return response.json();
}

async function deleteTask(id) {
    const response = await fetch(`${API}/tasks/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete task');
}

async function getTask(id) {
    const response = await fetch(`${API}/tasks/${id}`);
    if (!response.ok) throw new Error('Task not found');
    return response.json();
}

// Render Functions
function renderTasks(tasks) {
    if (tasks.length === 0) {
        elements.tasksContainer.innerHTML = '';
        elements.emptyState.classList.add('visible');
        return;
    }
    
    elements.emptyState.classList.remove('visible');
    elements.tasksContainer.innerHTML = tasks.map((task, index) => createTaskCard(task, index)).join('');
    
    // Add event listeners
    elements.tasksContainer.querySelectorAll('.task-btn.complete').forEach(btn => {
        btn.addEventListener('click', () => handleStatusChange(btn.dataset.id));
    });
    
    elements.tasksContainer.querySelectorAll('.task-btn.edit').forEach(btn => {
        btn.addEventListener('click', () => openEditModal(btn.dataset.id));
    });
    
    elements.tasksContainer.querySelectorAll('.task-btn.delete').forEach(btn => {
        btn.addEventListener('click', () => openDeleteModal(btn.dataset.id));
    });
}

function createTaskCard(task, index) {
    const statusLabel = task.status.replace('_', ' ');
    const dueDate = task.due_date ? formatDate(task.due_date) : 'No due date';
    const createdDate = formatDate(task.created_at.split('T')[0]);
    const isCompleted = task.status === 'completed';
    
    return `
        <div class="task-card priority-${task.priority} ${isCompleted ? 'completed' : ''}" style="animation-delay: ${index * 50}ms">
            <div class="task-header">
                <h3 class="task-title">${escapeHtml(task.title)}</h3>
                <div class="task-badges">
                    <span class="badge priority-${task.priority}">${task.priority}</span>
                    <span class="badge status-${task.status}">${statusLabel}</span>
                </div>
            </div>
            ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
            <div class="task-footer">
                <div class="task-meta">
                    <span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <path d="M16 2v4M8 2v4M3 10h18"/>
                        </svg>
                        ${dueDate}
                    </span>
                </div>
                <div class="task-actions">
                    ${!isCompleted ? `
                        <button class="task-btn complete" data-id="${task.id}" title="Mark complete">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                                <path d="M22 4L12 14.01l-3-3"/>
                            </svg>
                        </button>
                    ` : ''}
                    <button class="task-btn edit" data-id="${task.id}" title="Edit">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                    <button class="task-btn delete" data-id="${task.id}" title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Modal Functions
function openModal() {
    resetForm();
    document.getElementById('modal-title').textContent = 'New Task';
    elements.statusGroup.style.display = 'none';
    elements.taskModal.classList.add('active');
}

async function openEditModal(id) {
    try {
        const task = await getTask(id);
        
        document.getElementById('modal-title').textContent = 'Edit Task';
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-due').value = task.due_date || '';
        document.getElementById('task-status').value = task.status;
        
        document.querySelector(`input[name="task-priority"][value="${task.priority}"]`).checked = true;
        
        elements.statusGroup.style.display = 'block';
        elements.taskModal.classList.add('active');
    } catch (error) {
        showToast('Failed to load task', 'error');
    }
}

function closeModal() {
    elements.taskModal.classList.remove('active');
    resetForm();
}

function resetForm() {
    elements.taskForm.reset();
    document.getElementById('task-id').value = '';
    document.getElementById('p-medium').checked = true;
}

function openDeleteModal(id) {
    taskToDelete = id;
    elements.deleteModal.classList.add('active');
}

function closeDeleteModal() {
    elements.deleteModal.classList.remove('active');
    taskToDelete = null;
}

// Form Handlers
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const data = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value || null,
        priority: document.querySelector('input[name="task-priority"]:checked').value,
        due_date: document.getElementById('task-due').value || null
    };
    
    if (id) {
        data.status = document.getElementById('task-status').value;
    }
    
    try {
        if (id) {
            await updateTask(id, data);
            showToast('Task updated successfully', 'success');
        } else {
            await createTask(data);
            showToast('Task created successfully', 'success');
        }
        
        closeModal();
        loadTasks();
        loadStats();
    } catch (error) {
        showToast(id ? 'Failed to update task' : 'Failed to create task', 'error');
    }
}

async function handleStatusChange(id) {
    try {
        const task = await getTask(id);
        const nextStatus = getNextStatus(task.status);
        await updateTask(id, { status: nextStatus });
        showToast('Task updated', 'success');
        loadTasks();
        loadStats();
    } catch (error) {
        showToast('Failed to update task', 'error');
    }
}

async function confirmDelete() {
    if (!taskToDelete) return;
    
    try {
        await deleteTask(taskToDelete);
        showToast('Task deleted', 'success');
        closeDeleteModal();
        loadTasks();
        loadStats();
    } catch (error) {
        showToast('Failed to delete task', 'error');
    }
}

// Utility Functions
function getNextStatus(current) {
    const flow = { 'pending': 'in_progress', 'in_progress': 'completed', 'completed': 'completed' };
    return flow[current];
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${type === 'success' 
                    ? '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>'
                    : '<circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>'}
            </svg>
        </div>
        <span class="toast-message">${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Export functions for HTML onclick handlers
window.openModal = openModal;
window.closeModal = closeModal;
window.closeDeleteModal = closeDeleteModal;
