<script setup>
import { ref, onMounted, computed } from 'vue'
import Layout from '../components/Layout.vue'
import { taskService } from '../services/api'
import moment from 'moment'

const tasks = ref([])
const loading = ref(true)
const showNewTaskModal = ref(false)
const editingTask = ref(null)

const newTask = ref({
  title: '',
  description: '',
  priority: 'medium',
  start_time: '',
  end_time: ''
})

const selectedTasks = ref(new Set())
const searchQuery = ref('')
const viewMode = ref('list') // 'list', 'grid', 'calendar'
const sortBy = ref('date') // 'date', 'priority', 'title'
const sortOrder = ref('asc') // 'asc', 'desc'

onMounted(async () => {
  await fetchTasks()
})

const fetchTasks = async () => {
  try {
    loading.value = true
    const response = await taskService.getTasks()
    tasks.value = response.data
  } catch (error) {
    console.error('Error fetching tasks:', error)
  } finally {
    loading.value = false
  }
}

const filteredTasks = computed(() => {
  let filtered = [...tasks.value]
  
  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(task => 
      task.title.toLowerCase().includes(query) || 
      task.description?.toLowerCase().includes(query)
    )
  }
  
  // Apply sorting
  filtered.sort((a, b) => {
    let comparison = 0
    switch (sortBy.value) {
      case 'date':
        comparison = new Date(a.start_time || '') - new Date(b.start_time || '')
        break
      case 'priority':
        const priorityMap = { high: 3, medium: 2, low: 1 }
        comparison = (priorityMap[a.priority] || 0) - (priorityMap[b.priority] || 0)
        break
      case 'title':
        comparison = (a.title || '').localeCompare(b.title || '')
        break
    }
    return sortOrder.value === 'desc' ? -comparison : comparison
  })
  
  return filtered
})

const handleSubmit = async () => {
  try {
    if (editingTask.value) {
      await taskService.updateTask(editingTask.value.id, newTask.value)
    } else {
      await taskService.createTask(newTask.value)
    }
    await fetchTasks()
    closeModal()
  } catch (error) {
    console.error('Error saving task:', error)
  }
}

const startEdit = (task) => {
  editingTask.value = task
  newTask.value = {
    title: task.title,
    description: task.description || '',
    priority: task.priority,
    start_time: task.start_time ? moment(task.start_time).format('YYYY-MM-DDTHH:mm') : '',
    end_time: task.end_time ? moment(task.end_time).format('YYYY-MM-DDTHH:mm') : ''
  }
  showNewTaskModal.value = true
}

const deleteTask = async (id) => {
  if (confirm('Are you sure you want to delete this task?')) {
    try {
      await taskService.deleteTask(id)
      await fetchTasks()
    } catch (error) {
      console.error('Error deleting task:', error)
    }
  }
}

const closeModal = () => {
  showNewTaskModal.value = false
  editingTask.value = null
  newTask.value = {
    title: '',
    description: '',
    priority: 'medium',
    start_time: '',
    end_time: ''
  }
}

const getPriorityColor = (priority) => {
  switch (priority) {
    case 'high': return 'text-red-600'
    case 'medium': return 'text-yellow-600'
    case 'low': return 'text-green-600'
    default: return 'text-gray-600'
  }
}

const formatDateTime = (date) => {
  return moment(date).format('MMM D, YYYY h:mm A')
}

const toggleSelectAll = () => {
  if (selectedTasks.value.size === filteredTasks.value.length) {
    selectedTasks.value.clear()
  } else {
    selectedTasks.value = new Set(filteredTasks.value.map(task => task.id))
  }
}

const toggleTaskSelection = (taskId) => {
  if (selectedTasks.value.has(taskId)) {
    selectedTasks.value.delete(taskId)
  } else {
    selectedTasks.value.add(taskId)
  }
}

const handleKeyPress = (e) => {
  // Add keyboard shortcuts
  if (e.key === 'n' && e.ctrlKey) {
    e.preventDefault()
    showNewTaskModal.value = true
  } else if (e.key === 'Delete' && selectedTasks.value.size > 0) {
    e.preventDefault()
    if (confirm(`Are you sure you want to delete ${selectedTasks.value.size} selected tasks?`)) {
      deleteSelectedTasks()
    }
  }
}

const deleteSelectedTasks = async () => {
  try {
    for (const taskId of selectedTasks.value) {
      await taskService.deleteTask(taskId)
    }
    selectedTasks.value.clear()
    await fetchTasks()
  } catch (error) {
    console.error('Error deleting tasks:', error)
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyPress)
})
</script>

<template>  <Layout>
    <div class="h-full space-y-6">
      <!-- Header Section -->
      <div class="bg-white shadow rounded-lg p-6 sticky top-0 z-10">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <!-- Left side -->
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Tasks</h1>
            <p class="mt-1 text-gray-600">Manage your tasks and deadlines</p>
          </div>

          <!-- Right side -->
          <div class="flex items-center space-x-4">
            <!-- Search -->
            <div class="relative flex-1 lg:max-w-xs">
              <input
                type="text"
                v-model="searchQuery"
                placeholder="Search tasks..."
                class="w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 pl-10 pr-4 py-2"
              />
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            <!-- View Options -->
            <div class="flex items-center space-x-2 border rounded-lg p-1">
              <button
                @click="viewMode = 'list'"
                :class="[
                  'p-2 rounded-md',
                  viewMode === 'list' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900'
                ]"
                title="List View (Ctrl + 1)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </button>
              <button
                @click="viewMode = 'grid'"
                :class="[
                  'p-2 rounded-md',
                  viewMode === 'grid' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900'
                ]"
                title="Grid View (Ctrl + 2)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button
                @click="viewMode = 'calendar'"
                :class="[
                  'p-2 rounded-md',
                  viewMode === 'calendar' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900'
                ]"
                title="Calendar View (Ctrl + 3)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
            </div>

            <!-- Sort Options -->
            <div class="flex items-center space-x-2">
              <select
                v-model="sortBy"
                class="rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="date">Sort by Date</option>
                <option value="priority">Sort by Priority</option>
                <option value="title">Sort by Title</option>
              </select>
              <button
                @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
                class="p-2 rounded-md hover:bg-gray-100"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  :class="{ 'rotate-180': sortOrder === 'desc' }"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9M3 12h6" />
                </svg>
              </button>
            </div>

            <button
              @click="showNewTaskModal = true"
              class="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-150"
              title="New Task (Ctrl + N)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Task
            </button>
          </div>
        </div>

        <!-- Quick Filters -->
        <div class="mt-6 flex flex-wrap gap-4">
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            All Tasks
          </button>
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Today
          </button>
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            This Week
          </button>
          <button 
            class="px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            High Priority
          </button>
        </div>

        <!-- Batch Actions -->
        <div v-if="selectedTasks.size > 0" class="mt-4 flex items-center justify-between bg-blue-50 p-4 rounded-lg">
          <span class="text-sm text-blue-700">{{ selectedTasks.size }} tasks selected</span>
          <div class="flex items-center space-x-4">
            <button
              @click="deleteSelectedTasks"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Delete Selected
            </button>
            <button
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Mark Complete
            </button>
          </div>
        </div>
      </div>

      <!-- Tasks Content -->
      <div class="bg-white shadow rounded-lg overflow-hidden">
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
        
        <div v-else-if="filteredTasks.length === 0" class="flex flex-col items-center justify-center h-64">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 class="text-lg font-medium text-gray-900">No tasks found</h3>
          <p v-if="searchQuery" class="mt-1 text-gray-500">Try adjusting your search or filters</p>
          <p v-else class="mt-1 text-gray-500">Get started by creating your first task!</p>
          <button
            @click="showNewTaskModal = true"
            class="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Create Task
          </button>
        </div>

        <!-- List View -->
        <div v-else-if="viewMode === 'list'" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-300">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="relative py-4 pl-6 pr-3">
                  <input
                    type="checkbox"
                    :checked="selectedTasks.size === filteredTasks.length"
                    :indeterminate="selectedTasks.size > 0 && selectedTasks.size < filteredTasks.length"
                    @change="toggleSelectAll"
                    class="absolute left-6 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th scope="col" class="py-4 pl-6 pr-3 text-left text-sm font-semibold text-gray-900">Title & Description</th>
                <th scope="col" class="px-3 py-4 text-left text-sm font-semibold text-gray-900">Timeline</th>
                <th scope="col" class="px-3 py-4 text-left text-sm font-semibold text-gray-900">Priority</th>
                <th scope="col" class="px-3 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                <th scope="col" class="relative py-4 pl-3 pr-6">
                  <span class="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="task in filteredTasks" :key="task.id" :class=" [
                'hover:bg-gray-50 transition-colors duration-150',
                selectedTasks.has(task.id) ? 'bg-blue-50' : ''
              ]">
                <td class="relative py-4 pl-6 pr-3">
                  <input
                    type="checkbox"
                    :checked="selectedTasks.has(task.id)"
                    @change="toggleTaskSelection(task.id)"
                    class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </td>
                <td class="py-4 pl-6 pr-3">
                  <div class="flex items-center">
                    <div>
                      <div class="text-sm font-medium text-gray-900">{{ task.title }}</div>
                      <div class="text-sm text-gray-500">{{ task.description || 'No description' }}</div>
                    </div>
                  </div>
                </td>
                <td class="whitespace-nowrap px-3 py-4">
                  <div class="text-sm text-gray-900">
                    {{ task.start_time ? formatDateTime(task.start_time) : 'Not set' }}
                  </div>
                  <div class="text-sm text-gray-500">
                    to {{ task.end_time ? formatDateTime(task.end_time) : 'Not set' }}
                  </div>
                </td>
                <td class="px-3 py-4">
                  <span 
                    :class=" [
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      {
                        'bg-red-100 text-red-800': task.priority === 'high',
                        'bg-yellow-100 text-yellow-800': task.priority === 'medium',
                        'bg-green-100 text-green-800': task.priority === 'low'
                      }
                    ]"
                  >
                    {{ task.priority }}
                  </span>
                </td>
                <td class="px-3 py-4">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {{ task.status || 'Pending' }}
                  </span>
                </td>
                <td class="relative whitespace-nowrap py-4 pl-3 pr-6 text-right text-sm font-medium">
                  <div class="flex items-center justify-end space-x-3">
                    <button 
                      @click="startEdit(task)" 
                      class="text-blue-600 hover:text-blue-900 flex items-center"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit
                    </button>
                    <button 
                      @click="deleteTask(task.id)" 
                      class="text-red-600 hover:text-red-900 flex items-center"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Grid View -->
        <div v-else-if="viewMode === 'grid'" class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="task in filteredTasks" :key="task.id" :class=" [
              'relative rounded-lg border p-6 space-y-4 hover:shadow-md transition-shadow duration-150',
              selectedTasks.has(task.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            ]">
              <div class="flex items-start justify-between">
                <div class="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    :checked="selectedTasks.has(task.id)"
                    @change="toggleTaskSelection(task.id)"
                    class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <h3 class="text-base font-medium text-gray-900">{{ task.title }}</h3>
                    <p class="mt-1 text-sm text-gray-500">{{ task.description || 'No description' }}</p>
                  </div>
                </div>
                <div class="flex items-center space-x-2">
                  <button 
                    @click="startEdit(task)" 
                    class="text-gray-400 hover:text-blue-500"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button 
                    @click="deleteTask(task.id)" 
                    class="text-gray-400 hover:text-red-500"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              <div class="flex items-center space-x-4 text-sm">
                <span 
                  :class=" [
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    {
                      'bg-red-100 text-red-800': task.priority === 'high',
                      'bg-yellow-100 text-yellow-800': task.priority === 'medium',
                      'bg-green-100 text-green-800': task.priority === 'low'
                    }
                  ]"
                >
                  {{ task.priority }}
                </span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {{ task.status || 'Pending' }}
                </span>
              </div>

              <div class="text-sm text-gray-500">
                <div>{{ task.start_time ? formatDateTime(task.start_time) : 'Start time not set' }}</div>
                <div>{{ task.end_time ? formatDateTime(task.end_time) : 'End time not set' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Calendar View -->
        <div v-else class="p-6">
          <p class="text-center text-gray-500">Calendar view coming soon!</p>
        </div>
      </div>
    </div>    <!-- Task Modal -->
    <div v-if="showNewTaskModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <!-- Modal Header -->
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="p-2 bg-blue-100 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900">
              {{ editingTask ? 'Edit Task' : 'Create New Task' }}
            </h3>
          </div>
          <button
            @click="closeModal"
            class="text-gray-400 hover:text-gray-500 focus:outline-none"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Content -->
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Left Column -->
              <div class="space-y-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Title</label>
                  <input
                    type="text"
                    v-model="newTask.title"
                    required
                    placeholder="Enter task title"
                    class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    v-model="newTask.description"
                    rows="4"
                    placeholder="Enter task description"
                    class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base"
                  ></textarea>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700">Priority</label>
                  <div class="mt-1 flex space-x-4">
                    <label class="flex items-center">
                      <input type="radio" v-model="newTask.priority" value="low" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                      <span class="ml-2 text-sm text-gray-700">Low</span>
                    </label>
                    <label class="flex items-center">
                      <input type="radio" v-model="newTask.priority" value="medium" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                      <span class="ml-2 text-sm text-gray-700">Medium</span>
                    </label>
                    <label class="flex items-center">
                      <input type="radio" v-model="newTask.priority" value="high" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                      <span class="ml-2 text-sm text-gray-700">High</span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- Right Column -->
              <div class="space-y-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Timeline</label>
                  <div class="mt-1 grid grid-cols-1 gap-4">
                    <div>
                      <label class="block text-xs text-gray-500 mb-1">Start Time</label>
                      <input
                        type="datetime-local"
                        v-model="newTask.start_time"
                        class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base"
                      />
                    </div>
                    <div>
                      <label class="block text-xs text-gray-500 mb-1">End Time</label>
                      <input
                        type="datetime-local"
                        v-model="newTask.end_time"
                        class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Reminders</label>
                  <div class="space-y-2">
                    <label class="flex items-center">
                      <input type="checkbox" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                      <span class="ml-2 text-sm text-gray-700">15 minutes before</span>
                    </label>
                    <label class="flex items-center">
                      <input type="checkbox" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                      <span class="ml-2 text-sm text-gray-700">1 hour before</span>
                    </label>
                    <label class="flex items-center">
                      <input type="checkbox" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                      <span class="ml-2 text-sm text-gray-700">1 day before</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end space-x-3">
          <button
            type="button"
            @click="closeModal"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            @click="handleSubmit"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {{ editingTask ? 'Save Changes' : 'Create Task' }}
          </button>
        </div>
      </div>
    </div>
  </Layout>
</template>
