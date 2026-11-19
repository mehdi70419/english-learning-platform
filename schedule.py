from apscheduler.schedulers.background import BackgroundScheduler

from connection_database import Sessionlocal
from datetime import datetime, timezone
from discussion_session_model import DiscussionSession
from discussion_topic_model import DiscussionTopic
from student_discussion_vote_model import StudentDiscussionVote
from discussion_session_registration_model import FreeDiscussionRegistration
from user_model import User
from sqlalchemy.orm import Session
from sqlalchemy import func





scheduler = BackgroundScheduler()



def background_task_function_called_by_schedular():
    db = Sessionlocal()
    try:

        helper_automatically_select_winning_topic(db)

    finally:
        db.close()


scheduler.add_job(background_task_function_called_by_schedular,
                       trigger="interval",
                       minutes=5
                       )


#we don't want to stop the endpoint if at each iteration sqlalchemy returns an empty list of qualifying votes
#so we use continue which means at each iteration if sqlalchemy returns an empty list of qualifyng votes
#continue means skip current iteration or skip current discussion session and move to the next iteration or next discussion session
#we don't stop the whole endpoint
#There is one important qualification: continue is available only inside a loop, and it does not mean that we should replace every HTTPException with continue.
#No qualifying votes for one session? Use continue, because we want to process the other sessions.
#when sqlalchemy send select for number of votes per topic it returns a list of tuples first value of each tuple represents the topic_id and
#the second value represents number of votes for that topic at each iteration or for each discussion session
#if sqlalchemy returns no qualifying vote then at each iteration sqlalchmey send a select to retrive offered topics belonging to that
#discussion session and python loops through topics to find the winning topic if discussion session has no offered topics
#python executes else statement and continue which means python doesn't execute the remaining parts of endpoint and move to next iteration
#if the initial SELECT retrieves no eligible sessions, the loop does nothing, and db.commit() completes without any data modification

def helper_automatically_select_winning_topic(db:Session):
    current_time = datetime.now(timezone.utc)
    db_discussion_sessions = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.voting_closes_at <= current_time,
                                                                DiscussionSession.chosen_topic_id == None).all()

    for i in db_discussion_sessions:
             number_of_votes_per_topic = (db.query(StudentDiscussionVote.discussion_topic_id, func.count(StudentDiscussionVote.id)).
                                     group_by(StudentDiscussionVote.discussion_topic_id).
                                     filter(StudentDiscussionVote.discussion_session_id == i.id,
                                     StudentDiscussionVote.user.has(User.discussion_registrations.
                                     any( (FreeDiscussionRegistration.status == "approved") &
                                    (FreeDiscussionRegistration.discussion_session_id == i.id) ) )).all())
             if not number_of_votes_per_topic:
                  db_already_existing_offerred_topics_for_discussion_session = ( db.query(DiscussionTopic).filter
                                                                                 (DiscussionTopic.offered_sessions.
                                                                            any(DiscussionSession.id == i.id) ).all() )
                  if db_already_existing_offerred_topics_for_discussion_session:
                      winning_topic = db_already_existing_offerred_topics_for_discussion_session[0]
                      for k in db_already_existing_offerred_topics_for_discussion_session:
                          if k.id < winning_topic.id :
                              winning_topic = k
                          else:
                              winning_topic = winning_topic

                      i.chosen_topic_id = winning_topic.id

                  else:
                         continue


             else:
                    winning_tuple = number_of_votes_per_topic[0]
                    for j in number_of_votes_per_topic:
                        if (j[1] > winning_tuple[1]) or (j[1] == winning_tuple[1] and j[0] < winning_tuple[0]):
                             winning_tuple = j
                        else:
                             winning_tuple = winning_tuple

                    winning_topic_id = winning_tuple[0]
                    i.chosen_topic_id = winning_topic_id

    db.commit()
    return db_discussion_sessions


def start_scheduler():
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()