import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import Tasks from '../views/Tasks.vue'
import Meetings from '../views/Meetings.vue'
import Chat from '../views/Chat.vue'

const routes = [
    {
        path: '/',
        redirect: '/login'
    },
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    {
        path: '/register',
        name: 'Register',
        component: Register
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
    },
    {
        path: '/tasks',
        name: 'Tasks',
        component: Tasks,
        meta: { requiresAuth: true }
    },
    {
        path: '/meetings',
        name: 'Meetings',
        component: Meetings,
        meta: { requiresAuth: true }
    },
    {
        path: '/chat',
        name: 'Chat',
        component: Chat,
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')
    if (to.matched.some(record => record.meta.requiresAuth) && !token) {
        next('/login')
    } else {
        next()
    }
})

export default router
