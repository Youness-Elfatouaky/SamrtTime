<script setup>
import { ref, onMounted, computed } from 'vue'
import Layout from '../components/Layout.vue'
import { taskService, meetingService } from '../services/api'
import moment from 'moment'

const tasks = ref([])
const meetings = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [tasksResponse, meetingsResponse] = await Promise.all([
      taskService.getTasks(),
      meetingService.getMeetings()
    ])
    tasks.value = tasksResponse.data
    meetings.value = meetingsResponse.data
  } catch (error) {
    console.error('Error fetching data:', error)
  } finally {
    loading.value = false
  }
})

const formatDateTime = (date) => {
  return moment(date).format('MMM D, YYYY h:mm A')
}

const getPriorityColor = (priority) => {
  switch (priority) {
    case 'high': return 'text-red-600'
    case 'medium': return 'text-yellow-600'
    case 'low': return 'text-green-600'
    default: return 'text-gray-600'
  }
}

// Computed property to combine and sort today's tasks and meetings
const todayEvents = computed(() => {
  const today = moment().startOf('day')
  const tomorrow = moment().add(1, 'day').startOf('day')

  // Convert tasks to calendar events
  const taskEvents = tasks.value
    .filter(task => {
      const taskDate = moment(task.end_time)
      return taskDate.isSameOrAfter(today) && taskDate.isBefore(tomorrow)
    })
    .map(task => ({
      ...task,
      type: 'task',
      start_time: task.start_time || task.end_time, // Use end_time as fallback if no start_time
    }))

  // Convert meetings to calendar events
  const meetingEvents = meetings.value
    .filter(meeting => {
      const meetingDate = moment(meeting.start_time)
      return meetingDate.isSameOrAfter(today) && meetingDate.isBefore(tomorrow)
    })
    .map(meeting => ({
      ...meeting,
      type: 'meeting'
    }))

  // Combine and sort by start time
  return [...taskEvents, ...meetingEvents]
    .sort((a, b) => moment(a.start_time).valueOf() - moment(b.start_time).valueOf())
})

// Computed property to process events and handle overlaps
const processedEvents = computed(() => {
  const events = todayEvents.value
  const timeSlots = new Map() // Track events by 30-minute slots
  const processed = []

  events.forEach(event => {
    const startTime = moment(event.start_time)
    const endTime = moment(event.end_time)
    const startSlot = startTime.hours() * 2 + Math.floor(startTime.minutes() / 30)
    const endSlot = endTime.hours() * 2 + Math.ceil(endTime.minutes() / 30)
    let column = 0

    // Find first available column
    while (true) {
      let columnTaken = false
      for (let slot = startSlot; slot < endSlot; slot++) {
        const key = `${slot}-${column}`
        if (timeSlots.has(key)) {
          columnTaken = true
          break
        }
      }
      if (!columnTaken) break
      column++
    }

    // Mark time slots as taken
    for (let slot = startSlot; slot < endSlot; slot++) {
      timeSlots.set(`${slot}-${column}`, event.id)
    }

    // Find max columns for this time range
    let maxColumns = 1
    for (let slot = startSlot; slot < endSlot; slot++) {
      let cols = 0
      while (timeSlots.has(`${slot}-${cols}`)) cols++
      maxColumns = Math.max(maxColumns, cols)
    }

    processed.push({
      ...event,
      column,
      totalColumns: maxColumns,
      startSlot,
      endSlot
    })
  })

  return processed
})

// Method to calculate event position and height
const getEventStyle = (event) => {
  const startTime = moment(event.start_time)
  const endTime = moment(event.end_time)
  const startMinutes = startTime.hours() * 60 + startTime.minutes()
  const durationMinutes = endTime.diff(startTime, 'minutes')
  const columnWidth = 100 / event.totalColumns // percentage width
  const hourHeight = 64 // 2 * 32px for each hour (allowing for 30-minute precision)

  return {
    top: `${(startMinutes / 30) * (hourHeight / 2)}px`,
    height: `${Math.max((durationMinutes / 30) * (hourHeight / 2), 24)}px`,
    left: `${event.column * columnWidth}%`,
    width: `${columnWidth - 1}%`, // Subtract 1% for gap
    minHeight: '24px',
  }
}

// Computed property to get current time position in pixels
const getCurrentTimePosition = computed(() => {
  const now = moment()
  const minutes = now.hours() * 60 + now.minutes()
  return (minutes / 30) * 32 // 32px per 30 minutes
})

// Computed property to organize events by hour
const eventsByHour = computed(() => {
  const hourSlots = Array(24).fill(null).map(() => []);
  
  todayEvents.value.forEach(event => {
    const startHour = moment(event.start_time).hour();
    const endHour = moment(event.end_time).hour();
    
    for (let hour = startHour; hour <= endHour; hour++) {
      hourSlots[hour].push({
        ...event,
        isStart: hour === startHour,
        isEnd: hour === endHour,
        startMinutes: hour === startHour ? moment(event.start_time).minutes() : 0,
        endMinutes: hour === endHour ? moment(event.end_time).minutes() : 59
      });
    }
  });
  
  return hourSlots;
});

// Compute current hour for highlighting
const currentHour = computed(() => {
  return moment().hour();
});
</script>

<template>  <Layout>
    <div class="h-full space-y-6">
      <!-- Welcome Section -->
      <div class="bg-white shadow rounded-lg p-6">
        <h1 class="text-2xl font-semibold text-gray-900">Welcome to SmartTime</h1>
        <p class="mt-2 text-gray-600">Today is {{ moment().format('dddd, MMMM D, YYYY') }}</p>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Tasks Section -->
        <div class="bg-white shadow rounded-lg p-6 lg:col-span-1">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-medium text-gray-900">Recent Tasks</h2>
            <router-link 
              to="/tasks" 
              class="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
            >
              View all
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </router-link>
          </div>
          <div v-if="loading" class="text-center py-4">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
          <div v-else-if="tasks.length === 0" class="text-center py-8">
            <div class="text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p class="text-gray-500">No tasks found</p>
            </div>
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="task in tasks.slice(0, 5)" 
              :key="task.id" 
              class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-150"
            >
              <div class="flex items-center space-x-4">
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900">
                    {{ task.title }}
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    Due: {{ formatDateTime(task.start_time) }}
                  </p>
                </div>
                <div 
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    {
                      'bg-red-100 text-red-800': task.priority === 'high',
                      'bg-yellow-100 text-yellow-800': task.priority === 'medium',
                      'bg-green-100 text-green-800': task.priority === 'low'
                    }
                  ]"
                >
                  {{ task.priority }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Meetings Section - Takes 2 columns on desktop -->
        <div class="bg-white shadow rounded-lg p-6 lg:col-span-2">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-medium text-gray-900">Upcoming Meetings</h2>
            <router-link 
              to="/meetings" 
              class="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
            >
              View all
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </router-link>
          </div>
          <div v-if="loading" class="text-center py-4">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
          <div v-else-if="meetings.length === 0" class="text-center py-8">
            <div class="text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p class="text-gray-500">No meetings scheduled</p>
            </div>
          </div>
          <div v-else class="grid gap-4 grid-cols-1 md:grid-cols-2">
            <div 
              v-for="meeting in meetings.slice(0, 6)" 
              :key="meeting.id" 
              class="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-150"
            >
              <div class="flex items-start space-x-4">
                <div class="flex-shrink-0">
                  <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <span class="text-blue-600 text-lg">
                      {{ meeting.title.charAt(0).toUpperCase() }}
                    </span>
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900">
                    {{ meeting.title }}
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    {{ formatDateTime(meeting.start_time) }}
                  </p>
                  <p v-if="meeting.location" class="text-xs text-gray-500 mt-1 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {{ meeting.location }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>      </div>

      <!-- Today's Calendar Section -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-medium text-gray-900">Today's Schedule</h2>
          <div class="text-sm text-gray-500">
            {{ moment().format('dddd, MMMM D') }}
          </div>
        </div>
        
        <!-- Calendar Grid -->
        <div class="grid grid-cols-[80px_1fr] gap-2">
          <div class="space-y-4">
            <!-- Time markers column -->
            <div v-for="hour in 24" :key="hour" class="h-16 flex items-center justify-end pr-2">
              <span class="text-sm text-gray-500">{{ (hour - 1).toString().padStart(2, '0') }}:00</span>
            </div>
          </div>
          
          <!-- Events column -->
          <div class="space-y-4">
            <div v-for="(events, hour) in eventsByHour" :key="hour" 
              class="h-16 flex items-center gap-2 pl-2"
              :class=" [
                hour === currentHour ? 'bg-blue-50' : 'bg-gray-50',
                'rounded'
              ]"
            >
              <template v-if="events.length > 0">
                <div v-for="event in events" :key="event.id"
                  class="flex-1 px-3 py-1 rounded text-xs flex items-center gap-2"
                  :class=" [
                    event.type === 'meeting' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700',
                  ]"
                >
                  <span class="font-medium truncate">{{ event.title }}</span>
                  <span class="whitespace-nowrap text-[10px] opacity-75">
                    {{ event.isStart ? moment(event.start_time).format('HH:mm') : '' }}
                    {{ event.isStart || event.isEnd ? '-' : '→' }}
                    {{ event.isEnd ? moment(event.end_time).format('HH:mm') : '' }}
                  </span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<style scoped>
/* Remove scrollbar styles as they're no longer needed */
</style>
