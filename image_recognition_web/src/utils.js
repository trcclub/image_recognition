import jpeg from 'jpeg-js'

export default {
  rosImageMsgToBase64 (msg) {
    var rawImageData = Uint8Array.from(atob(msg.data), c => c.charCodeAt(0))

    var frameData = new Buffer(msg.width * msg.height * 4)
    var i = 0
    var j = 0
    while (i < frameData.length) {
      frameData[i++] = rawImageData[j + 2] // red
      frameData[i++] = rawImageData[j + 1] // green
      frameData[i++] = rawImageData[j] // blue
      frameData[i++] = 0xFF // alpha - ignored in JPEGs
      j += 3
    }

    var rawImage = {
      data: frameData,
      width: msg.width,
      height: msg.height
    }
    var jpegImage = jpeg.encode(rawImage, 100)
    return jpegImage.data.toString('base64')
  }
}
