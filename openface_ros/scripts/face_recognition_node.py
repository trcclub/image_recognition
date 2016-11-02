#!/usr/bin/env python

import rospy
from cv_bridge import CvBridge, CvBridgeError

from image_recognition_msgs.srv import Recognize, Annotate
from image_recognition_msgs.msg import Recognition, CategoryProbability, CategoricalDistribution
from sensor_msgs.msg import RegionOfInterest
from std_srvs.srv import Empty

import cv2
import os
from datetime import datetime
import sys

from openface_ros.face_recognizer import FaceRecognizer, RecognizedFace


class OpenfaceROS:
    def __init__(self, align_path, net_path, save_images_folder):
        self._bridge = CvBridge()
        self._annotate_srv = rospy.Service('annotate', Annotate, self._annotate_srv)
        self._recognize_srv = rospy.Service('recognize', Recognize, self._recognize_srv)
        self._clear_srv = rospy.Service('clear', Empty, self._clear_srv)

        # Openface ROS
        self._face_recognizer = FaceRecognizer(align_path, net_path)

        if save_images_folder and not os.path.exists(save_images_folder):
            save_images_folder = os.path.expanduser(save_images_folder)
            os.makedirs(save_images_folder)

        self._save_images_folder = save_images_folder

        rospy.loginfo("OpenfaceROS initialized:")
        rospy.loginfo(" - dlib_align_path=%s", align_path)
        rospy.loginfo(" - openface_net_path=%s", net_path)
        rospy.loginfo(" - save_images_folder=%s", save_images_folder)

    def _annotate_srv(self, req):
        # Convert to opencv image
        try:
            bgr_image = self._bridge.imgmsg_to_cv2(req.image, "bgr8")
        except CvBridgeError as e:
            raise Exception("Could not convert to opencv image: %s" % str(e))

        for annotation in req.annotations:
            roi_image = bgr_image[annotation.roi.y_offset:annotation.roi.y_offset+annotation.roi.height,
                                  annotation.roi.x_offset:annotation.roi.x_offset + annotation.roi.width]

            if self._save_images_folder:
                now = datetime.now()
                cv2.imwrite("%s/%s_annotate_%s.jpeg" % (self._save_images_folder, now.strftime("%Y-%m-%d-%H-%M-%S-%f"),
                                                        annotation.label), roi_image)

            try:
                self._face_recognizer.train(roi_image, annotation.label)
            except Exception as e:
                raise Exception("Could not get representation of face image: %s" % str(e))

            rospy.loginfo("Succesfully learned face of '%s'" % annotation.label)

        return {}

    def _clear_srv(self, req):
        self._face_recognizer.clear_trained_faces()
        return {}

    def _recognize_srv(self, req):
        # Convert to opencv image
        try:
            bgr_image = self._bridge.imgmsg_to_cv2(req.image, "bgr8")
        except CvBridgeError as e:
            raise Exception("Could not convert to opencv image: %s" % str(e))

        # Call openface
        face_recognitions = self._face_recognizer.recognize(bgr_image)

        # Fill recognitions
        recognitions = []
        for face_recognition in face_recognitions:

            if self._save_images_folder:
                now = datetime.now()
                cv2.imwrite("%s/recognize_%s.jpeg" %
                            (self._save_images_folder, now.strftime("%Y-%m-%d-%H-%M-%S-%f"), face_recognition.image))

            recognitions.append(Recognition(
                categorical_distribution=CategoricalDistribution(
                    unknown_probability=0.0,  # TODO: When is it unknown?
                    probabilities=[CategoryProbability(label=l2.label, probability=1.0/l2.distance)
                                   for l2 in face_recognition.l2_distances]
                ),
                roi=RegionOfInterest(
                    x_offset=face_recognition.roi.x_offset,
                    y_offset=face_recognition.roi.y_offset,
                    width=face_recognition.roi.width,
                    height=face_recognition.roi.height
                )
            ))

        # Service response
        return {"recognitions": recognitions}

if __name__ == '__main__':

    rospy.init_node("face_recognition")

    try:
        dlib_shape_predictor_path = rospy.get_param("~align_path",
                                                    "~/openface/models/dlib/shape_predictor_68_face_landmarks.dat")
        openface_neural_network_path = rospy.get_param("~net_path", "~/openface/models/openface/nn4.small2.v1.t7")
        save_images = rospy.get_param("~save_images", False)

        save_images_folder = None
        if save_images:
            save_images_folder = rospy.get_param("~save_images_folder", "/tmp/openface")
    except KeyError as e:
        rospy.logerr("Parameter %s not found" % e)
        sys.exit(1)

    openface_ros = OpenfaceROS(dlib_shape_predictor_path,
                               openface_neural_network_path,
                               save_images_folder)
    rospy.spin()
