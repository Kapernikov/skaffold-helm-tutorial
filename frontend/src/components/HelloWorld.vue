<template>
  <v-container>
    <v-row class="text-center">
      <v-col cols="12">
        <v-img
          :src="require('../assets/logo.svg')"
          class="my-3"
          contain
          height="200"
        />
      </v-col>

      <v-col class="mb-4">
        <h1 class="display-2 font-weight-bold mb-3">
          Welcome to Vuetify
        </h1>

        <p class="subheading font-weight-regular">
          The current time is <span>{{current_time}}</span>
        </p>
         <v-btn
            text
            color="primary"
            @click=" getTime();"
          >request time</v-btn>

      </v-col>

    </v-row>
  </v-container>
</template>

<script>
  import axios from 'axios';
  export default {
    name: 'HelloWorld',

    data: () => ({ 
      current_time : "placeholder"
    }),
    methods: {
      getTime: function() {
        axios
          .get('http://localhost:9999/time')
          .then(response => (this.current_time = response["data"]["current"]))
      }
    }
  }
</script>
