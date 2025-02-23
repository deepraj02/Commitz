sealed class HomePageState {
  const HomePageState();
}

class HomePageStateInitial extends HomePageState {}

class HomePageStateLoading extends HomePageState {}

class HomePageStateSuccess<T> extends HomePageState {
  final T event;

  HomePageStateSuccess(this.event);
}
