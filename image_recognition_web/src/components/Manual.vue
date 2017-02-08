<template>
  <div class="container">
    <img :src="image" class="img-responsive thumbnail" v-show="activeRequest" />
    <form v-on:submit.prevent v-show="activeRequest">
      <div class="input-group">
        <span class="input-group-btn">
          <button class="btn" type="submit" @click="submit">Send response</button>
        </span>
        <input type="text" class="form-control" placeholder="What is this?" v-model="classification">
      </div><!-- /input-group -->
    </form>
    <div class="well well-sm" v-show="!activeRequest">Waiting for service call on /manual ...</div>
  </div><!-- /.container -->
</template>

<script>

import ROSLIB from 'roslib'
import ros from '../ros.js'
import utils from '../utils.js'

var manualService = new ROSLIB.Service({
  ros: ros,
  name: '/manual',
  serviceType: 'image_recognition_msgs/Recognize'
})

export default {
  name: 'Manual',
  data () {
    return {
      activeRequest: null,
      image: '',
      classification: ''
    }
  },
  methods: {
    submit () {
      manualService.returnService()
    }
  },
  mounted () {
    var context = this

    // Required for delaying service
    manualService._serviceResponse = function (rosbridgeRequest) {
      var service = this
      context.activeRequest = rosbridgeRequest

      var base64ImageData = utils.rosImageMsgToBase64(rosbridgeRequest.args.image)
      context.image = `data:image/jpeg;base64,${base64ImageData}`

      this.timeout = setTimeout(() => {
        service.returnService()
      }, 30000) // Return after 30 seconds automatically
    }

    // Required for delaying service
    manualService.returnService = function () {
      var response = {}
      var success = this._serviceCallback(context.activeRequest.args, response)

      var call = {
        op: 'service_response',
        service: this.name,
        values: new ROSLIB.ServiceResponse(response),
        result: success
      }

      console.log(call, response)

      if (context.activeRequest.id) {
        call.id = context.activeRequest.id
      }

      this.ros.callOnConnection(call)

      clearTimeout(this.timeout)
      context.activeRequest = null
    }

    manualService.advertise((req, resp) => {
      resp.recognitions = [{
        roi: {
          width: req.image.width,
          height: req.image.height
        },
        categorical_distribution: {
          probabilities: [{
            label: `${context.classification}`,
            probability: 1.0
          }],
          unknown_probability: 0
        }
      }]

      return true
    })
  }
}
</script>
