import ROSLIB from 'roslib'

import {hostname} from 'os'

// Private variables
const host = hostname() || 'localhost'

export default new ROSLIB.Ros({
  url: `ws://${host}:9090`
})
