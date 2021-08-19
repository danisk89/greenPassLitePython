from imutils.video import VideoStream
from imutils.video import FPS
import cv2
from pyzbar.pyzbar import decode
import datetime
from dec_green import DecodeGreen

#vs = VideoStream(src=0,usePiCamera=True).start()
vs = VideoStream(src=0,usePiCamera=True,resolution=(1280,720)).start()
fps = FPS().start()
detector = cv2.QRCodeDetector()
getGreen = DecodeGreen()
modeVideoDate = None
while True:
    frame = vs.read()
    if frame is not None:
        bs = decode(frame)
        for bar in bs:
            if modeVideoDate is None:
                bdata = bar.data.decode("utf-8")
                btype = bar.type
                modeVideoDate = datetime.datetime.now()
                res = getGreen.main(bdata)
                print(res)
        if modeVideoDate is not None:
            now = datetime.datetime.now()
            past = modeVideoDate + datetime.timedelta(0, 5)
            if datetime.datetime.timestamp(past) <= datetime.datetime.timestamp(now) :
                modeVideoDate = None
        cv2.imshow("Frame", frame)
    if cv2.waitKey(10) & 0xFF == ord(mySettings.keyToExit):
        break
    fps.update()
fps.stop()
cv2.destroyAllWindows()
vs.stop()
